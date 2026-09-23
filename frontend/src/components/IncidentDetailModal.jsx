import React, { useState } from 'react';
import { X, Sparkles, AlertCircle, CheckCircle2, Clock, Server, User, Tag } from 'lucide-react';
import { summarizeIncident } from '../api';

export default function IncidentDetailModal({ isOpen, onClose, incident }) {
  const [loadingAi, setLoadingAi] = useState(false);
  const [postMortem, setPostMortem] = useState(null);

  if (!isOpen || !incident) return null;

  const handleGeneratePostMortem = async () => {
    setLoadingAi(true);
    try {
      const res = await summarizeIncident(incident.number || incident.sys_id);
      setPostMortem(res.post_mortem);
    } catch (err) {
      alert(`Failed to generate post-mortem: ${err.message}`);
    } finally {
      setLoadingAi(false);
    }
  };

  const getPriorityBadge = (p) => {
    const map = {
      1: { label: 'P1 - Critical', cls: 'badge-p1' },
      2: { label: 'P2 - High', cls: 'badge-p2' },
      3: { label: 'P3 - Medium', cls: 'badge-p3' },
      4: { label: 'P4 - Low', cls: 'badge-p4' }
    };
    const item = map[p] || { label: `P${p}`, cls: 'badge-p3' };
    return <span className={`badge ${item.cls}`}>{item.label}</span>;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '780px' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span style={{ fontSize: '18px', fontWeight: '800', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                {incident.number}
              </span>
              {getPriorityBadge(incident.priority)}
              <span className="badge" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-primary)' }}>
                {incident.state}
              </span>
              {incident.sla_breached && (
                <span className="badge badge-p1">SLA Breached</span>
              )}
              {incident.servicenow_url && (
                <a
                  href={incident.servicenow_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="badge"
                  style={{
                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                    color: '#a5b4fc',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                  title="Open live ticket in ServiceNow"
                >
                  <span>Open in ServiceNow</span>
                  <span style={{ fontSize: '10px' }}>↗</span>
                </a>
              )}
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)', lineHeight: '1.4' }}>
              {incident.short_description}
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Details Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '14px',
          padding: '16px',
          backgroundColor: 'var(--bg-elevated)',
          borderRadius: '10px',
          marginBottom: '20px',
          fontSize: '13px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={15} color="#06b6d4" />
            <span style={{ color: 'var(--text-muted)' }}>Configuration Item:</span>
            <span style={{ fontWeight: '600' }}>{incident.cmdb_ci || 'General IT'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tag size={15} color="#818cf8" />
            <span style={{ color: 'var(--text-muted)' }}>Assignment Group:</span>
            <span style={{ fontWeight: '600' }}>{incident.assignment_group || 'Service Desk'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <User size={15} color="#10b981" />
            <span style={{ color: 'var(--text-muted)' }}>Assigned To:</span>
            <span style={{ fontWeight: '600' }}>{incident.assigned_to || 'Unassigned'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={15} color="#f59e0b" />
            <span style={{ color: 'var(--text-muted)' }}>Opened:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>{incident.opened_at ? incident.opened_at.replace('T', ' ').slice(0, 16) : 'N/A'}</span>
          </div>
        </div>

        {/* Description */}
        <div style={{ marginBottom: '22px' }}>
          <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Incident Description & Work Notes
          </span>
          <p style={{
            fontSize: '13px',
            color: 'var(--text-secondary)',
            marginTop: '6px',
            lineHeight: '1.6',
            backgroundColor: 'rgba(0,0,0,0.2)',
            padding: '12px',
            borderRadius: '8px'
          }}>
            {incident.description || 'No additional technical description attached to this ticket.'}
          </p>
        </div>

        {/* AI Summarization Button / Section */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <h4 style={{ fontSize: '15px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} color="#6366f1" />
                AI Incident Post-Mortem & RCA
              </h4>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Generative AI deep-dive: Impact, Root Cause, Resolution & Lessons Learned
              </span>
            </div>
            {!postMortem && (
              <button
                className="btn-primary"
                onClick={handleGeneratePostMortem}
                disabled={loadingAi}
                style={{ fontSize: '12px', padding: '8px 16px' }}
              >
                {loadingAi ? 'Synthesizing...' : 'Generate SRE Analysis'}
              </button>
            )}
          </div>

          {loadingAi && (
            <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '13px' }}>
              <div style={{ display: 'inline-block', width: '20px', height: '20px', border: '2px solid #6366f1', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', marginRight: '8px' }} />
              Synthesizing root cause telemetry and operational context...
            </div>
          )}

          {postMortem && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="structured-card">
                <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                  Operational Impact
                </span>
                <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '4px' }}>
                  {postMortem.impact}
                </p>
              </div>

              <div className="structured-card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', color: '#f87171', textTransform: 'uppercase' }}>
                  Identified Root Cause
                </span>
                <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '4px' }}>
                  {postMortem.root_cause}
                </p>
              </div>

              <div className="structured-card" style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', color: '#34d399', textTransform: 'uppercase' }}>
                  Resolution Summary
                </span>
                <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '4px' }}>
                  {postMortem.resolution}
                </p>
              </div>

              <div className="structured-card" style={{ borderColor: 'rgba(99, 102, 241, 0.3)' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', color: '#a5b4fc', textTransform: 'uppercase' }}>
                  Lessons Learned & Prevention
                </span>
                <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginTop: '4px' }}>
                  {postMortem.lessons_learned}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
