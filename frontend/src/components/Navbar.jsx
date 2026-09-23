import React from 'react';
import { Sparkles, Moon, Sun, Database, ShieldCheck, Terminal } from 'lucide-react';

export default function Navbar({ activeTab, onOpenQueryInspector, lastQuery, theme, setTheme }) {
  const titles = {
    chat: 'Natural Language Incident Assistant',
    dashboard: 'Incident Analytics & KPI Dashboard',
    recurring: 'Recurring Incidents & Root Cause Detection',
    outage: 'Outage Timeline & Investigation Assistant',
    reports: 'Executive Incident Reporting',
    settings: 'ServiceNow & AI System Settings',
  };

  return (
    <header className="top-navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <h2 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--text-primary)' }}>
          {titles[activeTab] || 'Incident Analytics'}
        </h2>
        <span style={{
          fontSize: '11px',
          padding: '2px 8px',
          borderRadius: '4px',
          background: 'rgba(99, 102, 241, 0.1)',
          color: '#a5b4fc',
          border: '1px solid rgba(99, 102, 241, 0.2)'
        }}>
          v1.0 Production
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {lastQuery && (
          <button 
            className="btn-secondary"
            onClick={onOpenQueryInspector}
            style={{ fontSize: '12px', padding: '6px 12px' }}
            title="Inspect generated ServiceNow encoded query"
          >
            <Terminal size={14} color="#06b6d4" />
            <span>ServiceNow Query</span>
          </button>
        )}

        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: 'var(--text-primary)'
          }}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* User Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '4px 10px',
          background: 'var(--bg-elevated)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{
            width: '26px',
            height: '26px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '11px',
            fontWeight: '700',
            color: '#fff'
          }}>
            IT
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', lineHeight: '1.2' }}>Ops Commander</span>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Capgemini Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
}
