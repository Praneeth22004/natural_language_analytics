import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Terminal, ArrowRight, ExternalLink, RefreshCw, Cpu, RotateCcw, History } from 'lucide-react';
import { sendChatMessage, resetChatSession } from '../api';
import MarkdownRenderer from '../components/MarkdownRenderer';

const generateSessionId = () => 'sn_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now().toString(36);

export default function ChatAssistantPage({ onInspectQuery, onSelectIncident }) {
  const [sessionId, setSessionId] = useState(() => {
    return sessionStorage.getItem('sn_chat_session_id') || generateSessionId();
  });
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: (
        "Hello! I am your **ServiceNow Incident AI Assistant** powered by **NVIDIA AI**.\n\n" +
        "I can execute live ServiceNow queries, analyze incidents, detect recurring clusters, and generate SRE post-mortems directly from operational data.\n\n" +
        "Click any prompt below or type your question:"
      ),
      suggestions: [
        "Ticket a ServiceNow incident: Oracle database connection timeout on SAP ORA01 (P1)",
        "Show all P1 critical incidents",
        "Summarize INC0000001",
        "Show open problem tickets",
        "Show CMDB configuration items",
        "Identify recurring incidents and root causes"
      ]
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    sessionStorage.setItem('sn_chat_session_id', sessionId);
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleRestartChat = async () => {
    if (resetting || loading) return;
    setResetting(true);
    try {
      await resetChatSession(sessionId);
    } catch (err) {
      console.warn("Session reset notice:", err);
    }
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([
      {
        id: 'welcome_' + Date.now(),
        role: 'assistant',
        content: (
          "🔄 **Chat Ended & Session Restarted**\n\n" +
          "All conversational context and memory have been cleared, and a fresh session has begun. " +
          "How can I assist your ServiceNow IT operations today?\n\n" +
          "Click any prompt below or type your question:"
        ),
        suggestions: [
          "Ticket a ServiceNow incident: Oracle database connection timeout on SAP ORA01 (P1)",
          "Show all P1 critical incidents",
          "Summarize INC0000001",
          "Show open problem tickets",
          "Show CMDB configuration items",
          "Identify recurring incidents and root causes"
        ]
      }
    ]);
    setInput('');
    setResetting(false);
  };

  const handleSend = async (queryText = null) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsgId = Date.now().toString();
    const newMessages = [
      ...messages,
      { id: userMsgId, role: 'user', content: textToSend }
    ];
    setMessages(newMessages);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(textToSend, sessionId);
      
      // If user invoked natural-language session reset, synchronize session ID
      if (response.structured_data?.session_reset) {
        const newId = generateSessionId();
        setSessionId(newId);
      }

      setMessages([
        ...newMessages,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response_text,
          structured_data: response.structured_data,
          sysparm_query: response.sysparm_query,
          intent: response.intent,
          execution_time_ms: response.execution_time_ms,
          suggestions: response.suggestions || []
        }
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ Failed to execute query: ${err.message}. Please verify the backend is running.`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [];
  const turnCount = messages.filter(m => m.role === 'user').length;

  return (
    <div className="page-body">
      <div className="chat-window">
        {/* Chat Control Header */}
        <div className="chat-header">
          <div className="chat-header-left">
            <div className="chat-header-icon-wrap">
              <Sparkles size={18} />
            </div>
            <div className="chat-header-info">
              <div className="chat-header-title">
                <span>ServiceNow Incident AI Copilot</span>
                <span className="chat-session-badge">
                  <span className="chat-session-pulse" />
                  Active Session
                </span>
              </div>
              <div className="chat-memory-badge">
                <History size={12} />
                <span>
                  {turnCount === 0 ? "Memory fresh" : `${turnCount} exchange${turnCount === 1 ? '' : 's'} memorized`}
                </span>
                <span style={{ opacity: 0.35 }}>•</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10.5px', opacity: 0.65 }}>
                  {sessionId.slice(0, 16)}...
                </span>
              </div>
            </div>
          </div>

          <div className="chat-header-right">
            <button
              className="btn-restart-chat"
              onClick={handleRestartChat}
              disabled={loading || resetting}
              title="End current chat, clear conversational memory, and restart fresh"
            >
              <RotateCcw size={13} style={resetting ? { animation: 'spin 1s linear infinite' } : {}} />
              <span>{resetting ? 'Restarting...' : 'End Chat & Restart'}</span>
            </button>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-bubble ${msg.role}`}>
              {/* Message Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                {msg.role === 'assistant' ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={15} color="#818cf8" />
                    <span style={{ fontSize: '12px', fontWeight: '700', color: '#a5b4fc' }}>Incident AI Engine</span>
                  </div>
                ) : (
                  <span style={{ fontSize: '12px', fontWeight: '700', opacity: 0.9 }}>You</span>
                )}

                {msg.sysparm_query && (
                  <button
                    onClick={() => onInspectQuery({
                      natural_query: msg.content,
                      sysparm_query: msg.sysparm_query,
                      intent: msg.intent,
                      execution_time_ms: msg.execution_time_ms
                    })}
                    style={{
                      marginLeft: 'auto',
                      background: 'rgba(6, 182, 212, 0.1)',
                      border: '1px solid rgba(6, 182, 212, 0.3)',
                      borderRadius: '4px',
                      color: '#38bdf8',
                      padding: '2px 8px',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Terminal size={11} />
                    <span>sysparm_query</span>
                  </button>
                )}
              </div>

              {/* Message Content Body */}
              <div style={{ lineHeight: '1.6' }}>
                <MarkdownRenderer content={msg.content} />
              </div>

              {/* Render Structured Breakdown Card if present */}
              {msg.structured_data?.breakdown && (
                <div className="structured-card">
                  <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Priority Breakdown
                  </span>
                  <div className="breakdown-grid">
                    <div className="breakdown-pill" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                      <span className="count" style={{ color: '#f87171' }}>{msg.structured_data.breakdown.Critical}</span>
                      <span className="label">Critical (P1)</span>
                    </div>
                    <div className="breakdown-pill" style={{ borderColor: 'rgba(249, 115, 22, 0.3)' }}>
                      <span className="count" style={{ color: '#fb923c' }}>{msg.structured_data.breakdown.High}</span>
                      <span className="label">High (P2)</span>
                    </div>
                    <div className="breakdown-pill" style={{ borderColor: 'rgba(234, 179, 8, 0.3)' }}>
                      <span className="count" style={{ color: '#facc15' }}>{msg.structured_data.breakdown.Medium}</span>
                      <span className="label">Medium (P3)</span>
                    </div>
                    <div className="breakdown-pill" style={{ borderColor: 'rgba(59, 130, 246, 0.3)' }}>
                      <span className="count" style={{ color: '#60a5fa' }}>{msg.structured_data.breakdown.Low}</span>
                      <span className="label">Low (P4)</span>
                    </div>
                    {msg.structured_data.breakdown.Planning !== undefined && (
                      <div className="breakdown-pill" style={{ borderColor: 'rgba(139, 92, 246, 0.3)' }}>
                        <span className="count" style={{ color: '#a78bfa' }}>{msg.structured_data.breakdown.Planning}</span>
                        <span className="label">Planning (P5)</span>
                      </div>
                    )}
                  </div>

                  {/* Sample Incidents click to inspect */}
                  {msg.structured_data.sample_incidents?.length > 0 && (
                    <div style={{ marginTop: '10px' }}>
                      <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                        Retrieved Tickets (Click for AI Post-Mortem):
                      </span>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {msg.structured_data.sample_incidents.map((inc) => (
                          <div
                            key={inc.sys_id || inc.number}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              background: 'var(--bg-elevated)',
                              border: '1px solid var(--border-subtle)',
                              borderRadius: '6px',
                              overflow: 'hidden'
                            }}
                          >
                            <button
                              onClick={() => onSelectIncident(inc)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                padding: '5px 8px',
                                fontSize: '11px',
                                color: 'var(--text-primary)',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px'
                              }}
                              title="Open AI Post-Mortem & SRE Analysis"
                            >
                              <span style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: '700' }}>{inc.number}</span>
                              {inc.cmdb_ci && (
                                <>
                                  <span>•</span>
                                  <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>{inc.cmdb_ci}</span>
                                </>
                              )}
                            </button>
                            {inc.servicenow_url && (
                              <a
                                href={inc.servicenow_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                  padding: '5px 7px',
                                  borderLeft: '1px solid var(--border-subtle)',
                                  color: '#a5b4fc',
                                  textDecoration: 'none',
                                  display: 'flex',
                                  alignItems: 'center',
                                  background: 'rgba(99, 102, 241, 0.1)'
                                }}
                                title="Open this incident directly in ServiceNow"
                              >
                                <ExternalLink size={11} />
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Follow-up Suggestions */}
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600' }}>Suggested Next Steps:</span>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                    {msg.suggestions.map((sug, i) => (
                      <button
                        key={i}
                        className="prompt-chip"
                        onClick={() => handleSend(sug)}
                        style={{ fontSize: '11px', padding: '4px 10px' }}
                      >
                        {sug}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="chat-bubble assistant">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '16px',
                  height: '16px',
                  border: '2px solid #6366f1',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Interpreting natural language & executing ServiceNow MCP query...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar & Suggested Prompt Chips */}
        <div className="chat-input-container">
          <div className="chip-row">
            {samplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                className="prompt-chip"
                onClick={() => handleSend(prompt)}
                disabled={loading}
              >
                {prompt}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="chat-input-row"
            style={{ marginTop: '8px' }}
          >
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything in plain English, e.g. 'What incidents were reported?'"
              disabled={loading}
            />
            <button type="submit" className="btn-primary" disabled={loading || !input.trim()}>
              <Send size={16} />
              <span>Ask AI</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
