import React from 'react';
import {
  MessageSquare,
  LayoutDashboard,
  Repeat,
  AlertTriangle,
  FileText,
  Settings,
  Layers,
  Radio,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, systemMode }) {
  const menuItems = [
    { id: 'chat', label: 'Chat Assistant', icon: MessageSquare, badge: 'AI' },
    { id: 'dashboard', label: 'Incident Analytics', icon: LayoutDashboard },
    // { id: 'recurring', label: 'Recurring & RCA', icon: Repeat },
    // { id: 'outage', label: 'Outage Investigation', icon: AlertTriangle },
    { id: 'reports', label: 'Executive Reports', icon: FileText },
    { id: 'settings', label: 'Admin Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ padding: '22px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
        }}>
          <Layers size={20} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '15px', fontWeight: '700', lineHeight: '1.2' }}>IncidentAI</h1>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ServiceNow Analytics</span>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ padding: '16px 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', padding: '8px 12px', letterSpacing: '0.05em' }}>
          Operations
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? '600' : '500',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                textAlign: 'left'
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icon size={18} color={isActive ? '#6366f1' : '#94a3b8'} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                  color: '#ffffff'
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* ServiceNow Connection Indicator Footer */}
      <div style={{ padding: '16px', borderTop: '1px solid var(--border-subtle)', backgroundColor: 'rgba(0, 0, 0, 0.15)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Data Source</span>
          <span className={`badge ${systemMode?.includes('Live') ? 'badge-live' : 'badge-simulation'}`}>
            <Radio size={10} />
            {systemMode?.includes('Live') ? 'Live PDI' : 'Demo Engine'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-secondary)' }}>
          <CheckCircle2 size={12} color="#10b981" />
          <span>MCP Protocol Active</span>
        </div>
      </div>
    </aside>
  );
}
