import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Clock, 
  Server, 
  CheckCircle2, 
  ShieldAlert, 
  Search, 
  Layers, 
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { investigateOutage } from '../api';

export default function OutageInvestigationPage() {
  const [service, setService] = useState('Email (MailServerUS)');
  const [outageData, setOutageData] = useState(null);
  const [loading, setLoading] = useState(true);

  const runInvestigation = async (srv = service) => {
    setLoading(true);
    try {
      const res = await investigateOutage(srv);
      setOutageData(res);
    } catch (err) {
      console.error('Error investigating outage:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runInvestigation('Email');
  }, []);

  const sampleServices = ['Email (MailServerUS)', 'ApplicationServerPeopleSoft', 'Oracle / SAP DB', 'Core Switches'];

  return (
    <div className="page-body">
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={24} color="#f59e0b" />
          Major Outage & Downtime Investigation Assistant
        </h2>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Automated multi-service correlation, timeline reconstruction, and outage blast radius analysis
        </span>
      </div>

      {/* Target Service Quick Select */}
      <div className="glass-card" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>
              Select Outage Incident Target:
            </span>
            {sampleServices.map((srv) => (
              <button
                key={srv}
                onClick={() => {
                  setService(srv);
                  runInvestigation(srv);
                }}
                className={`badge ${service === srv ? 'badge-p1' : ''}`}
                style={{
                  padding: '6px 12px',
                  cursor: 'pointer',
                  border: service === srv ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
                  background: service === srv ? 'rgba(239, 68, 68, 0.2)' : 'var(--bg-elevated)'
                }}
              >
                {srv}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              className="chat-input"
              style={{ width: '220px', padding: '6px 12px', fontSize: '12px' }}
              value={service}
              onChange={(e) => setService(e.target.value)}
              placeholder="Search service/application..."
            />
            <button
              className="btn-primary"
              style={{ padding: '6px 14px', fontSize: '12px' }}
              onClick={() => runInvestigation(service)}
            >
              <Search size={14} />
              <span>Investigate</span>
            </button>
          </div>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ display: 'inline-block', width: '24px', height: '24px', border: '2px solid #6366f1', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Reconstructing historical outage telemetry from ServiceNow records...</div>
        </div>
      )}

      {/* Outage Investigation Content */}
      {!loading && outageData && outageData.found && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
          {/* Left Column: Outage Metadata & Blast Radius */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="glass-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                <span className="badge badge-p1">P1 Outage</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: '#38bdf8' }}>
                  {outageData.incident_number}
                </span>
                <span className="badge badge-p1">SLA Breached</span>
              </div>

              <h3 style={{ fontSize: '18px', fontWeight: '800', lineHeight: '1.4', marginBottom: '14px' }}>
                {outageData.title}
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div style={{ padding: '12px', background: 'var(--bg-elevated)', borderRadius: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Primary Affected CI</span>
                  <div style={{ fontSize: '14px', fontWeight: '700', marginTop: '4px', color: 'var(--accent-cyan)' }}>
                    {outageData.primary_ci}
                  </div>
                </div>

                <div style={{ padding: '12px', background: 'var(--bg-elevated)', borderRadius: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Outage Duration</span>
                  <div style={{ fontSize: '14px', fontWeight: '700', marginTop: '4px', color: '#f87171' }}>
                    {outageData.duration}
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Cascading Impacted Services
                </span>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                  {(outageData.impacted_applications || []).map((app, i) => (
                    <span key={i} className="badge" style={{ backgroundColor: 'rgba(99, 102, 241, 0.1)', color: '#a5b4fc' }}>
                      <Server size={11} />
                      {app}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', color: '#10b981', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle2 size={13} />
                  Resolution & Post-Mortem Summary
                </span>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: '1.6' }}>
                  {outageData.resolution_summary}
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Outage Timeline */}
          <div className="glass-card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Clock size={16} color="#6366f1" />
              Incident Timeline & SRE Bridge Log
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '16px' }}>
              Chronological sequence of failure detection, triage, and resolution
            </span>

            <div className="timeline">
              {(outageData.timeline || []).map((item, idx) => (
                <div key={idx} className="timeline-item">
                  <div className="timeline-dot" style={{ backgroundColor: idx === 0 ? '#ef4444' : (idx === outageData.timeline.length - 1 ? '#10b981' : '#6366f1') }} />
                  <div className="timeline-time">{item.timestamp ? item.timestamp.replace('T', ' ').slice(0, 19) : ''}</div>
                  <div className="timeline-event">{item.event}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {!loading && outageData && !outageData.found && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '40px' }}>
          <CheckCircle2 size={36} color="#10b981" style={{ margin: '0 auto 12px auto' }} />
          <h3 style={{ fontSize: '16px', fontWeight: '700' }}>{outageData.message}</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '6px' }}>
            No major Sev-1 outage tickets were logged for '{service}' during this window.
          </p>
        </div>
      )}
    </div>
  );
}
