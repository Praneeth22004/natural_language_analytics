import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Database, 
  Key, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  RefreshCw, 
  Cpu, 
  Terminal,
  Activity,
  Sparkles
} from 'lucide-react';
import { fetchSettings, updateSettings, testServiceNowConnection, testLlmConnection, fetchAuditLogs } from '../api';

export default function AdminSettingsPage() {
  const [settingsData, setSettingsData] = useState({
    instance_url: '',
    username: '',
    password: '',
    use_mock_fallback: true,
    llm_provider: 'semantic_engine',
    openai_api_key: '',
    nvidia_api_key: '',
    nvidia_model: 'meta/llama-3.2-11b-vision-instruct',
    nvidia_base_url: 'https://integrate.api.nvidia.com/v1'
  });

  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionResult, setConnectionResult] = useState(null);
  const [testingLlm, setTestingLlm] = useState(false);
  const [llmTestResult, setLlmTestResult] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [aiSaveSuccess, setAiSaveSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadSettingsAndLogs = async () => {
    setLoading(true);
    try {
      const [sRes, logsRes] = await Promise.all([
        fetchSettings(),
        fetchAuditLogs()
      ]);
      setSettingsData(prev => ({
        ...prev,
        instance_url: sRes.instance_url || '',
        username: sRes.username || '',
        use_mock_fallback: sRes.use_mock_fallback !== undefined ? sRes.use_mock_fallback : true,
        llm_provider: sRes.llm_provider || 'semantic_engine',
        nvidia_model: sRes.nvidia_model || 'meta/llama-3.2-11b-vision-instruct',
        nvidia_base_url: sRes.nvidia_base_url || 'https://integrate.api.nvidia.com/v1'
      }));
      setAuditLogs(logsRes || []);
    } catch (err) {
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettingsAndLogs();
  }, []);

  const handleSave = async (e) => {
    if (e) e.preventDefault();
    try {
      await updateSettings(settingsData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert(`Failed to save settings: ${err.message}`);
    }
  };

  const handleAiSave = async (e) => {
    if (e) e.preventDefault();
    try {
      await updateSettings(settingsData);
      setAiSaveSuccess(true);
      setTimeout(() => setAiSaveSuccess(false), 3000);
    } catch (err) {
      alert(`Failed to save AI settings: ${err.message}`);
    }
  };

  const handleTestLlm = async () => {
    setTestingLlm(true);
    setLlmTestResult(null);
    try {
      await updateSettings(settingsData);
      const res = await testLlmConnection(settingsData.llm_provider);
      setLlmTestResult(res);
    } catch (err) {
      setLlmTestResult({
        success: false,
        provider: settingsData.llm_provider,
        message: err.message
      });
    } finally {
      setTestingLlm(false);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionResult(null);
    try {
      const res = await testServiceNowConnection();
      setConnectionResult(res);
    } catch (err) {
      setConnectionResult({
        success: false,
        mode: 'Connection Failed',
        message: err.message
      });
    } finally {
      setTestingConnection(false);
    }
  };

  return (
    <div className="page-body">
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Settings size={24} color="#6366f1" />
          ServiceNow PDI & AI Infrastructure Settings
        </h2>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Manage your ServiceNow Personal Developer Instance credentials, LLM provider orchestration, and audit logs
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px', marginBottom: '28px' }}>
        {/* Form: ServiceNow Credentials */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Database size={18} color="#06b6d4" />
            <h3 style={{ fontSize: '16px', fontWeight: '700' }}>ServiceNow REST API Credentials</h3>
          </div>

          <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                ServiceNow Instance URL
              </label>
              <input
                type="text"
                className="chat-input"
                style={{ width: '100%' }}
                placeholder="https://devXXXXX.service-now.com"
                value={settingsData.instance_url}
                onChange={(e) => setSettingsData({ ...settingsData, instance_url: e.target.value })}
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Your personal developer instance domain (e.g. dev123456.service-now.com)
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                  Username
                </label>
                <input
                  type="text"
                  className="chat-input"
                  style={{ width: '100%' }}
                  placeholder="admin"
                  value={settingsData.username}
                  onChange={(e) => setSettingsData({ ...settingsData, username: e.target.value })}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                  Password
                </label>
                <input
                  type="password"
                  className="chat-input"
                  style={{ width: '100%' }}
                  placeholder="••••••••••••"
                  value={settingsData.password}
                  onChange={(e) => setSettingsData({ ...settingsData, password: e.target.value })}
                />
              </div>
            </div>

            {/* Mode Toggle */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: '8px',
              marginTop: '4px'
            }}>
              <div>
                <span style={{ fontSize: '13px', fontWeight: '600', display: 'block' }}>
                  Enterprise Demo Dataset Fallback
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Auto-switch to realistic seed data if PDI is asleep or credentials are empty
                </span>
              </div>
              <input
                type="checkbox"
                checked={settingsData.use_mock_fallback}
                onChange={(e) => setSettingsData({ ...settingsData, use_mock_fallback: e.target.checked })}
                style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: '#6366f1' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
              <button type="submit" className="btn-primary" style={{ flex: 1 }}>
                <span>Save Configuration</span>
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleTestConnection}
                disabled={testingConnection}
                style={{ flex: 1 }}
              >
                <RefreshCw size={14} className={testingConnection ? 'spin-icon' : ''} />
                <span>{testingConnection ? 'Verifying...' : 'Test Connection'}</span>
              </button>
            </div>

            {saveSuccess && (
              <div style={{ color: '#10b981', fontSize: '12px', textAlign: 'center', fontWeight: '600' }}>
                ✓ Settings updated successfully
              </div>
            )}
          </form>

          {/* Test Connection Output Diagnostic */}
          {connectionResult && (
            <div style={{
              marginTop: '16px',
              padding: '14px',
              borderRadius: '8px',
              backgroundColor: connectionResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${connectionResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                {connectionResult.success ? (
                  <CheckCircle2 size={16} color="#10b981" />
                ) : (
                  <AlertCircle size={16} color="#ef4444" />
                )}
                <span style={{ fontWeight: '700', fontSize: '13px', color: connectionResult.success ? '#10b981' : '#f87171' }}>
                  {connectionResult.mode}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {connectionResult.message}
              </p>
            </div>
          )}
        </div>

        {/* AI & LLM Engine Settings */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Cpu size={18} color="#818cf8" />
            <h3 style={{ fontSize: '16px', fontWeight: '700' }}>AI & MCP Orchestrator Settings</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                Active LLM Provider
              </label>
              <select
                className="chat-input"
                style={{ width: '100%', cursor: 'pointer' }}
                value={settingsData.llm_provider}
                onChange={(e) => setSettingsData({ ...settingsData, llm_provider: e.target.value })}
              >
                <option value="semantic_engine">Semantic Engine (Built-in High-Speed Fallback)</option>
                <option value="nvidia">NVIDIA NIM / AI Foundation (LLaMA 3.3, Nemotron, Mixtral)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="azure">Azure OpenAI Service</option>
                <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
                <option value="gemini">Google Gemini 1.5</option>
              </select>
            </div>

            {/* Provider-Specific Configuration: NVIDIA */}
            {settingsData.llm_provider === 'nvidia' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Sparkles size={14} color="#10b981" />
                  <span style={{ fontSize: '12px', fontWeight: '700', color: '#34d399', textTransform: 'uppercase' }}>
                    NVIDIA NIM / AI Catalog Configuration
                  </span>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                    NVIDIA API Key
                  </label>
                  <input
                    type="password"
                    className="chat-input"
                    style={{ width: '100%' }}
                    placeholder="nvapi-••••••••••••••••••••"
                    value={settingsData.nvidia_api_key}
                    onChange={(e) => setSettingsData({ ...settingsData, nvidia_api_key: e.target.value })}
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                    Generate from <a href="https://build.nvidia.com" target="_blank" rel="noopener noreferrer" style={{ color: '#38bdf8' }}>build.nvidia.com</a>. Required for NVIDIA hosted inference.
                  </span>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                    NVIDIA Model Name
                  </label>
                  <input
                    type="text"
                    className="chat-input"
                    style={{ width: '100%' }}
                    placeholder="meta/llama-3.2-11b-vision-instruct"
                    value={settingsData.nvidia_model}
                    onChange={(e) => setSettingsData({ ...settingsData, nvidia_model: e.target.value })}
                  />
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                    {[
                      { id: 'meta/llama-3.2-11b-vision-instruct', label: 'llama-3.2-11b (Low Tokens ★)' },
                      { id: 'nvidia/llama-3.1-nemotron-70b-instruct', label: 'nemotron-70b' },
                      { id: 'mistralai/mistral-large-2-instruct', label: 'mistral-large-2' },
                      { id: 'meta/llama2-70b', label: 'llama2-70b' }
                    ].map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => setSettingsData({ ...settingsData, nvidia_model: m.id })}
                        style={{
                          fontSize: '10px',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          background: settingsData.nvidia_model === m.id ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                          border: `1px solid ${settingsData.nvidia_model === m.id ? '#10b981' : 'var(--border-subtle)'}`,
                          color: settingsData.nvidia_model === m.id ? '#34d399' : 'var(--text-muted)',
                          cursor: 'pointer'
                        }}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                    NVIDIA Base URL (API Catalog or Local NIM)
                  </label>
                  <input
                    type="text"
                    className="chat-input"
                    style={{ width: '100%' }}
                    placeholder="https://integrate.api.nvidia.com/v1"
                    value={settingsData.nvidia_base_url}
                    onChange={(e) => setSettingsData({ ...settingsData, nvidia_base_url: e.target.value })}
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                    Default: <code>https://integrate.api.nvidia.com/v1</code>. Point to your self-hosted NIM instance (e.g. <code>http://localhost:8000/v1</code>) if running on-premise.
                  </span>
                </div>
              </div>
            )}

            {/* Provider-Specific Configuration: OpenAI & others */}
            {settingsData.llm_provider !== 'nvidia' && settingsData.llm_provider !== 'semantic_engine' && (
              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                  {settingsData.llm_provider.toUpperCase()} API Key
                </label>
                <input
                  type="password"
                  className="chat-input"
                  style={{ width: '100%' }}
                  placeholder="sk-••••••••••••••••••••"
                  value={settingsData.openai_api_key}
                  onChange={(e) => setSettingsData({ ...settingsData, openai_api_key: e.target.value })}
                />
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                  Leave empty to run 100% on the internal deterministic Semantic Engine.
                </span>
              </div>
            )}

            {/* Save and Test Connection for AI Orchestration */}
            <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
              <button
                type="button"
                className="btn-primary"
                onClick={handleAiSave}
                style={{ flex: 1 }}
              >
                <span>Save AI Configuration</span>
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleTestLlm}
                disabled={testingLlm}
                style={{ flex: 1 }}
              >
                <RefreshCw size={14} className={testingLlm ? 'spin-icon' : ''} />
                <span>{testingLlm ? 'Testing LLM...' : 'Test AI Connection'}</span>
              </button>
            </div>

            {aiSaveSuccess && (
              <div style={{ color: '#10b981', fontSize: '12px', textAlign: 'center', fontWeight: '600' }}>
                ✓ AI configuration updated successfully
              </div>
            )}

            {/* Test Connection Output Diagnostic for LLM */}
            {llmTestResult && (
              <div style={{
                marginTop: '4px',
                padding: '12px 14px',
                borderRadius: '8px',
                backgroundColor: llmTestResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                border: `1px solid ${llmTestResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  {llmTestResult.success ? (
                    <CheckCircle2 size={16} color="#10b981" />
                  ) : (
                    <AlertCircle size={16} color="#ef4444" />
                  )}
                  <span style={{ fontWeight: '700', fontSize: '13px', color: llmTestResult.success ? '#10b981' : '#f87171' }}>
                    {llmTestResult.success ? 'LLM Provider Online' : 'LLM Test Failed'}
                  </span>
                  {llmTestResult.latency_ms !== undefined && (
                    <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {llmTestResult.latency_ms}ms
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  {llmTestResult.message}
                </p>
                {llmTestResult.sample_output && (
                  <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', background: 'rgba(0,0,0,0.3)', padding: '6px 8px', borderRadius: '4px', color: '#a5b4fc', marginTop: '6px' }}>
                    Output: {llmTestResult.sample_output}
                  </div>
                )}
              </div>
            )}

            <div style={{
              padding: '14px',
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              fontSize: '12px'
            }}>
              <div style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={14} color="#10b981" />
                Active Model Context Protocol (MCP) Servers
              </div>
              <ul style={{ paddingLeft: '18px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                <li><code>servicenow_mcp_server</code> (Incident, Problem, CI Tools)</li>
                <li><code>analytics_mcp_server</code> (MTTR, MTBF, Clustering Tools)</li>
                <li><code>reporting_mcp_server</code> (PDF, DOCX, XLSX Export Tools)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Terminal size={16} color="#06b6d4" />
              Natural Language & Query Audit Trail
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Logged questions, generated ServiceNow sysparm_queries, execution latency, and return counts
            </span>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Natural Language Prompt</th>
                <th>Generated ServiceNow Query</th>
                <th>Status</th>
                <th>Latency</th>
                <th>Results</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    No audit records logged yet. Query something in the Chat Assistant!
                  </td>
                </tr>
              )}
              {auditLogs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                    {log.timestamp ? log.timestamp.replace('T', ' ').slice(0, 19) : ''}
                  </td>
                  <td style={{ fontWeight: '600' }}>{log.natural_query}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#38bdf8', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {log.generated_query || 'N/A'}
                  </td>
                  <td>
                    <span className="badge badge-live">{log.status}</span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {log.execution_time_ms}ms
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: '700' }}>
                    {log.records_returned}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
