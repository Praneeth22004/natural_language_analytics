import React from 'react';

export default function KpiCard({ title, value, subtext, variant = 'default', icon: Icon, trend }) {
  return (
    <div className={`kpi-card ${variant}`}>
      <div className="kpi-title">
        <span>{title}</span>
        {Icon && <Icon size={16} color="var(--text-muted)" />}
      </div>
      <div>
        <div className="kpi-value">{value}</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span className="kpi-subtext">{subtext}</span>
          {trend && (
            <span style={{
              fontSize: '11px',
              fontWeight: '600',
              color: trend.startsWith('+') ? '#ef4444' : '#10b981',
              backgroundColor: trend.startsWith('+') ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
              padding: '2px 6px',
              borderRadius: '4px'
            }}>
              {trend}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
