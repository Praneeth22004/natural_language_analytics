import React, { useState } from 'react';

/**
 * Donut Chart Component (for Priority Breakdown or State Distribution)
 */
export function DonutChart({ data, size = 180, strokeWidth = 24, centerLabel = "Total", centerValue }) {
  // data: [{ label: 'P1 Critical', value: 12, color: '#ef4444' }, ...]
  const total = data.reduce((sum, d) => sum + (d.value || 0), 0) || 1;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  let accumulatedAngle = 0;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
      <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {data.map((item, idx) => {
            const ratio = (item.value || 0) / total;
            const strokeDasharray = `${ratio * circumference} ${circumference}`;
            const strokeDashoffset = -accumulatedAngle * circumference;
            accumulatedAngle += ratio;

            return (
              <circle
                key={idx}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="transparent"
                stroke={item.color}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
                style={{ transition: 'stroke-dasharray 0.5s ease' }}
              />
            );
          })}
        </svg>
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none'
        }}>
          <span style={{ fontSize: '20px', fontWeight: '800', fontFamily: 'var(--font-heading)' }}>
            {centerValue !== undefined ? centerValue : total}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            {centerLabel}
          </span>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '130px' }}>
        {data.map((item, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '3px', backgroundColor: item.color }} />
              <span style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
            </div>
            <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Horizontal Bar Chart (for Assignment Groups or Application Rankings)
 */
export function HorizontalBarChart({ data, maxVal = null, barColor = "#6366f1" }) {
  // data: [{ label: 'Network Engineering', value: 34, color: optional }, ...]
  const maximum = maxVal || Math.max(...data.map(d => d.value || 0), 1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
      {data.map((item, idx) => {
        const percent = Math.round(((item.value || 0) / maximum) * 100);
        return (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-primary)', fontWeight: '500' }}>{item.label}</span>
              <span style={{ color: 'var(--text-muted)', fontWeight: '600' }}>{item.value}</span>
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: '999px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${percent}%`,
                height: '100%',
                background: item.color || `linear-gradient(90deg, ${barColor}, #06b6d4)`,
                borderRadius: '999px',
                transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)'
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Trend Line & Area Chart (for Monthly or Daily Incident Volume)
 */
export function TrendLineChart({ data, height = 180 }) {
  // data: [{ label: 'Aug', value: 25 }, { label: 'Sep', value: 42 }, ...]
  const [hoveredIndex, setHoveredIndex] = useState(null);
  if (!data || data.length === 0) return null;

  const width = 500;
  const paddingX = 40;
  const paddingY = 24;
  const innerWidth = width - paddingX * 2;
  const innerHeight = height - paddingY * 2;

  const values = data.map(d => d.value);
  const maxVal = Math.max(...values, 1);
  const minVal = 0;

  const points = data.map((d, i) => {
    const x = paddingX + (i / (data.length - 1 || 1)) * innerWidth;
    const y = height - paddingY - ((d.value - minVal) / (maxVal - minVal || 1)) * innerHeight;
    return { x, y, ...d };
  });

  // Construct SVG path line & closed area
  const linePath = points.reduce((acc, p, i) => {
    return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - paddingY} L ${points[0].x} ${height - paddingY} Z`;

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal Grid lines */}
        {[0, 0.5, 1].map((ratio, i) => {
          const y = height - paddingY - ratio * innerHeight;
          return (
            <line
              key={i}
              x1={paddingX}
              y1={y}
              x2={width - paddingX}
              y2={y}
              stroke="var(--border-subtle)"
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Gradient Area */}
        <path d={areaPath} fill="url(#areaGradient)" />

        {/* Solid Line */}
        <path
          d={linePath}
          fill="none"
          stroke="#6366f1"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {points.map((p, idx) => (
          <g key={idx} onMouseEnter={() => setHoveredIndex(idx)} onMouseLeave={() => setHoveredIndex(null)}>
            <circle
              cx={p.x}
              cy={p.y}
              r={hoveredIndex === idx ? 6 : 4}
              fill="#ffffff"
              stroke="#6366f1"
              strokeWidth="2"
              style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
            />
            {/* Label below axis */}
            <text
              x={p.x}
              y={height - 6}
              fontSize="10"
              fill="var(--text-muted)"
              textAnchor="middle"
              fontFamily="var(--font-mono)"
            >
              {p.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Tooltip on hover */}
      {hoveredIndex !== null && (
        <div style={{
          position: 'absolute',
          top: points[hoveredIndex].y - 32,
          left: `${(points[hoveredIndex].x / width) * 100}%`,
          transform: 'translateX(-50%)',
          backgroundColor: '#0f172a',
          color: '#fff',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: '700',
          border: '1px solid var(--border-strong)',
          pointerEvents: 'none',
          whiteSpace: 'nowrap'
        }}>
          {points[hoveredIndex].label}: {points[hoveredIndex].value} Incidents
        </div>
      )}
    </div>
  );
}
