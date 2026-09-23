import json
import logging
import time
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """Multi-provider LLM Client supporting NVIDIA NIM, OpenAI, Azure OpenAI, Anthropic, Gemini, or Offline Semantic Engine."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

    @property
    def active_provider(self) -> str:
        return (settings.LLM_PROVIDER or self.provider).lower()

    @property
    def active_model(self) -> str:
        prov = self.active_provider
        if prov == "nvidia":
            return settings.NVIDIA_MODEL
        elif prov == "openai":
            return settings.OPENAI_MODEL
        elif prov == "azure":
            return settings.AZURE_OPENAI_DEPLOYMENT
        elif prov == "anthropic":
            return settings.ANTHROPIC_MODEL
        elif prov == "gemini":
            return settings.GEMINI_MODEL
        return "Deterministic Semantic Engine"

    def is_available(self) -> bool:
        prov = self.active_provider
        if prov == "nvidia" and settings.NVIDIA_API_KEY:
            return True
        if prov == "openai" and settings.OPENAI_API_KEY:
            return True
        if prov == "azure" and settings.AZURE_OPENAI_API_KEY:
            return True
        if prov == "anthropic" and settings.ANTHROPIC_API_KEY:
            return True
        if prov == "gemini" and settings.GEMINI_API_KEY:
            return True
        return False

    async def generate_chat_completion(self,
                                       messages: List[Dict[str, str]],
                                       temperature: float = 0.2,
                                       max_tokens: int = 1000) -> Optional[str]:
        """Calls the configured LLM provider or returns None to engage the Semantic Engine."""
        provider = (settings.LLM_PROVIDER or self.provider).lower()

        # 1. NVIDIA (NVIDIA NIM / AI Foundation & API Catalog)
        if provider == "nvidia" and settings.NVIDIA_API_KEY:
            return await self._call_nvidia(messages, temperature, max_tokens)

        # 2. OpenAI
        elif provider == "openai" and settings.OPENAI_API_KEY:
            return await self._call_openai(messages, temperature, max_tokens)

        # 3. Azure OpenAI
        elif provider == "azure" and settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            return await self._call_azure(messages, temperature, max_tokens)

        # 4. Anthropic
        elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            return await self._call_anthropic(messages, temperature, max_tokens)

        # 5. Gemini
        elif provider == "gemini" and settings.GEMINI_API_KEY:
            return await self._call_gemini(messages, temperature, max_tokens)

        # Fallback to Built-in Semantic Engine
        return None

    async def _call_nvidia(self, messages: List[Dict[str, str]], temp: float, max_t: int) -> Optional[str]:
        base_url = (settings.NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model": settings.NVIDIA_MODEL,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_t
        }
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            return choices[0]["message"].get("content", "")
                    elif resp.status_code in [429, 500, 502, 503, 504] and attempt == 0:
                        await asyncio.sleep(0.6)
                        continue
                    else:
                        logger.warning(f"NVIDIA NIM API error [{resp.status_code}]: {resp.text}")
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                logger.error(f"Exception connecting to NVIDIA NIM API at {url}: {e}")
        return None

    async def _call_openai(self, messages: List[Dict[str, str]], temp: float, max_t: int) -> Optional[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_t
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"OpenAI API error [{resp.status_code}]: {resp.text}")
        except Exception as e:
            logger.error(f"Exception connecting to OpenAI API: {e}")
        return None

    async def _call_azure(self, messages: List[Dict[str, str]], temp: float, max_t: int) -> Optional[str]:
        endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        deploy = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        url = f"{endpoint}/openai/deployments/{deploy}/chat/completions?api-version=2024-02-15-preview"
        headers = {
            "api-key": settings.AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {"messages": messages, "temperature": temp, "max_tokens": max_t}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"Azure OpenAI API error [{resp.status_code}]: {resp.text}")
        except Exception as e:
            logger.error(f"Exception connecting to Azure OpenAI API: {e}")
        return None

    async def _call_anthropic(self, messages: List[Dict[str, str]], temp: float, max_t: int) -> Optional[str]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        # Format for Claude
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]
        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "system": system_msg,
            "messages": user_msgs,
            "max_tokens": max_t,
            "temperature": temp
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["content"][0]["text"]
                else:
                    logger.warning(f"Anthropic API error [{resp.status_code}]: {resp.text}")
        except Exception as e:
            logger.error(f"Exception connecting to Anthropic API: {e}")
        return None

    async def _call_gemini(self, messages: List[Dict[str, str]], temp: float, max_t: int) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        contents = []
        for m in messages:
            role = "user" if m["role"] in ["user", "system"] else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        payload = {"contents": contents, "generationConfig": {"temperature": temp, "maxOutputTokens": max_t}}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    logger.warning(f"Gemini API error [{resp.status_code}]: {resp.text}")
        except Exception as e:
            logger.error(f"Exception connecting to Gemini API: {e}")
        return None

    async def test_provider(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Performs a lightweight ping test to verify LLM provider configuration and connectivity."""
        target_provider = (provider_name or settings.LLM_PROVIDER or "semantic_engine").lower()
        test_messages = [{"role": "user", "content": "Reply with 'OK' and nothing else."}]

        if target_provider == "semantic_engine":
            return {
                "success": True,
                "provider": "semantic_engine",
                "model": "Deterministic Incident NLP & SRE Engine",
                "message": "Semantic Engine is active and operating with sub-millisecond local latency.",
                "latency_ms": 1
            }

        start_time = time.time()
        result = None

        if target_provider == "nvidia":
            if not settings.NVIDIA_API_KEY:
                return {
                    "success": False,
                    "provider": "nvidia",
                    "model": settings.NVIDIA_MODEL,
                    "message": "NVIDIA API Key is missing. Please provide your NVIDIA API key (nvapi-...) to connect."
                }
            result = await self._call_nvidia(test_messages, temp=0.1, max_t=20)
            latency = int((time.time() - start_time) * 1000)
            if result:
                return {
                    "success": True,
                    "provider": "nvidia",
                    "model": settings.NVIDIA_MODEL,
                    "endpoint": settings.NVIDIA_BASE_URL,
                    "message": f"Successfully connected to NVIDIA NIM ({settings.NVIDIA_MODEL}).",
                    "sample_output": result.strip()[:100],
                    "latency_ms": latency
                }
            return {
                "success": False,
                "provider": "nvidia",
                "model": settings.NVIDIA_MODEL,
                "message": f"Failed to connect to NVIDIA NIM at {settings.NVIDIA_BASE_URL}. Verify your API key and network connectivity."
            }

        elif target_provider == "openai":
            if not settings.OPENAI_API_KEY:
                return {
                    "success": False,
                    "provider": "openai",
                    "model": settings.OPENAI_MODEL,
                    "message": "OpenAI API Key is missing."
                }
            result = await self._call_openai(test_messages, temp=0.1, max_t=20)
            latency = int((time.time() - start_time) * 1000)
            if result:
                return {
                    "success": True,
                    "provider": "openai",
                    "model": settings.OPENAI_MODEL,
                    "message": f"Successfully connected to OpenAI ({settings.OPENAI_MODEL}).",
                    "sample_output": result.strip()[:100],
                    "latency_ms": latency
                }
            return {
                "success": False,
                "provider": "openai",
                "model": settings.OPENAI_MODEL,
                "message": "Failed to connect to OpenAI API. Verify your API key and model access."
            }

        elif target_provider == "azure":
            if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
                return {"success": False, "provider": "azure", "message": "Azure OpenAI credentials or endpoint missing."}
            result = await self._call_azure(test_messages, temp=0.1, max_t=20)
            latency = int((time.time() - start_time) * 1000)
            return {
                "success": bool(result),
                "provider": "azure",
                "message": "Azure OpenAI connection verified." if result else "Azure OpenAI call failed.",
                "latency_ms": latency
            }

        elif target_provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                return {"success": False, "provider": "anthropic", "message": "Anthropic API Key is missing."}
            result = await self._call_anthropic(test_messages, temp=0.1, max_t=20)
            latency = int((time.time() - start_time) * 1000)
            return {
                "success": bool(result),
                "provider": "anthropic",
                "message": "Anthropic connection verified." if result else "Anthropic call failed.",
                "latency_ms": latency
            }

        elif target_provider == "gemini":
            if not settings.GEMINI_API_KEY:
                return {"success": False, "provider": "gemini", "message": "Google Gemini API Key is missing."}
            result = await self._call_gemini(test_messages, temp=0.1, max_t=20)
            latency = int((time.time() - start_time) * 1000)
            return {
                "success": bool(result),
                "provider": "gemini",
                "message": "Google Gemini connection verified." if result else "Google Gemini call failed.",
                "latency_ms": latency
            }

        return {
            "success": False,
            "provider": target_provider,
            "message": f"Unsupported LLM provider: '{target_provider}'"
        }

llm_client = LLMClient()

