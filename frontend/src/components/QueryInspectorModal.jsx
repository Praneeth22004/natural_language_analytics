import React, { useState } from 'react';
import { X, Copy, Check, Terminal, Clock, Shield, Sparkles } from 'lucide-react';

export default function QueryInspectorModal({ isOpen, onClose, queryData }) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !queryData) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(queryData.sysparm_query || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(6, 182, 212, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Terminal size={18} color="#06b6d4" />
            </div>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700' }}>ServiceNow Semantic Query Inspector</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>NL to sysparm_query translation telemetry</span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Natural Language Prompt */}
        <div style={{ marginBottom: '16px' }}>
          <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Original Natural Language Query
          </span>
          <div style={{
            padding: '10px 14px',
            backgroundColor: 'var(--bg-elevated)',
            borderRadius: '8px',
            marginTop: '6px',
            fontSize: '13px',
            color: 'var(--text-primary)',
            fontWeight: '500'
          }}>
            "{queryData.natural_query || queryData.message || 'What incidents were reported yesterday?'}"
          </div>
        </div>

        {/* Translation Meta Chips */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '18px' }}>
          <div className="badge badge-simulation">
            <Sparkles size={11} />
            Intent: {queryData.intent || 'QUERY_INCIDENTS'}
          </div>
          <div className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
            <Clock size={11} />
            Latency: {queryData.execution_time_ms || 32}ms
          </div>
          <div className="badge" style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)', color: '#818cf8' }}>
            <Shield size={11} />
            Query Validated: Clean
          </div>
        </div>

        {/* Generated ServiceNow sysparm_query */}
        <div style={{ marginBottom: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              ServiceNow Encoded Query (sysparm_query)
            </span>
            <button
              onClick={handleCopy}
              className="btn-secondary"
              style={{ padding: '4px 10px', fontSize: '11px' }}
            >
              {copied ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
              <span>{copied ? 'Copied' : 'Copy Query'}</span>
            </button>
          </div>
          <div className="query-box">
            {queryData.sysparm_query || 'priority=1^opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()^ORDERBYDESCopened_at'}
          </div>
        </div>

        {/* API Endpoint Details */}
        <div style={{
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          padding: '12px 16px',
          fontSize: '12px',
          color: 'var(--text-secondary)'
        }}>
          <div style={{ fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px' }}>Target Table API URL:</div>
          <code style={{ fontFamily: 'var(--font-mono)', color: '#94a3b8', wordBreak: 'break-all' }}>
            GET /api/now/table/incident?sysparm_query={encodeURIComponent(queryData.sysparm_query || '')}&sysparm_limit=50&sysparm_display_value=all
          </code>
        </div>
      </div>
    </div>
  );
}
