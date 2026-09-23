import React, { useState, useEffect } from 'react';
import { 
  Repeat, 
  Target, 
  Layers, 
  Lightbulb, 
  CheckCircle2, 
  AlertOctagon, 
  TrendingUp, 
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { fetchRecurringClusters, fetchRcaLeaderboard } from '../api';

export default function RecurringAndRcaPage({ onSelectIncident }) {
  const [clustersData, setClustersData] = useState(null);
  const [rcaLeaderboard, setRcaLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [cRes, rRes] = await Promise.all([
          fetchRecurringClusters(),
          fetchRcaLeaderboard()
        ]);
        setClustersData(cRes);
        setRcaLeaderboard(rRes.leaderboard || []);
      } catch (err) {
        console.error('Error loading recurring data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const clusters = clustersData?.recurring_clusters || [];

  return (
    <div className="page-body">
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Repeat size={24} color="#6366f1" />
          Recurring Incident Clusters & Root Cause Intelligence
        </h2>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Automated semantic pattern clustering, noise reduction, and preventative corrective action recommendations
        </span>
      </div>

      {/* Summary KPI Highlights */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '28px'
      }}>
        <div className="glass-card" style={{ padding: '16px 20px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>
            Identified Clusters
          </span>
          <div style={{ fontSize: '26px', fontWeight: '800', margin: '6px 0', color: 'var(--accent-cyan)' }}>
            {clustersData?.total_clusters_detected ?? clusters.length} Distinct Patterns
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Grouped from live ServiceNow tickets</span>
        </div>

        <div className="glass-card" style={{ padding: '16px 20px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>
            Clustered Incident Volume
          </span>
          <div style={{ fontSize: '26px', fontWeight: '800', margin: '6px 0', color: '#f87171' }}>
            {clustersData?.total_clustered_incidents ?? 0} Live Incidents
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Across live monitored services</span>
        </div>

        <div className="glass-card" style={{ padding: '16px 20px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600' }}>
            Highest Repeat Culprit
          </span>
          <div style={{ fontSize: '17px', fontWeight: '800', margin: '8px 0', color: '#fb923c' }}>
            {clusters[0]?.affected_application || clustersData?.top_affected_application || 'Service Desk / Active Directory'}
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {clusters[0] ? `${clusters[0].occurrences} incidents: ${clusters[0].title}` : 'Grouped by live tickets'}
          </span>
        </div>
      </div>

      {/* Section 1: Recurring Clusters Cards */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '17px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} color="#6366f1" />
          Detected Recurring Incident Clusters
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: '20px' }}>
          {clusters.map((cluster) => (
            <div key={cluster.cluster_id} className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '3px',
                background: cluster.occurrences >= 20 ? 'linear-gradient(90deg, #ef4444, #f97316)' : 'linear-gradient(90deg, #6366f1, #06b6d4)'
              }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>
                    {cluster.title}
                  </h4>
                  <span style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontWeight: '600' }}>
                    Affected Application: {cluster.affected_application}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    fontSize: '18px',
                    fontWeight: '800',
                    fontFamily: 'var(--font-heading)',
                    color: cluster.occurrences >= 20 ? '#f87171' : '#38bdf8'
                  }}>
                    {cluster.occurrences}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>Occurrences</span>
                </div>
              </div>

              {/* Root Cause Callout */}
              <div style={{
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '8px',
                padding: '10px 14px',
                marginBottom: '12px',
                fontSize: '13px'
              }}>
                <span style={{ fontWeight: '700', color: '#f87171', display: 'block', marginBottom: '2px', fontSize: '11px', textTransform: 'uppercase' }}>
                  Identified Root Cause:
                </span>
                <span style={{ color: 'var(--text-primary)' }}>{cluster.root_cause}</span>
              </div>

              {/* AI Recommendation */}
              <div style={{
                backgroundColor: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                borderRadius: '8px',
                padding: '10px 14px',
                marginBottom: '14px',
                fontSize: '13px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                  <Lightbulb size={13} color="#a5b4fc" />
                  <span style={{ fontWeight: '700', color: '#a5b4fc', fontSize: '11px', textTransform: 'uppercase' }}>
                    AI Recommended Remediation:
                  </span>
                </div>
                <span style={{ color: 'var(--text-primary)' }}>{cluster.recommendation}</span>
              </div>

              {/* Status and Action */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                <span className="badge" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                  {cluster.status}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                  Trend: <strong>{cluster.trend}</strong>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Root Cause Leaderboard */}
      <div className="glass-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Target size={18} color="#06b6d4" />
              Root Cause Leaderboard
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Top systemic causes ranked by frequency and operational blast radius
            </span>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Root Cause Hypothesis</th>
                <th>Impacted Application</th>
                <th>Category</th>
                <th>Incidents</th>
                <th>Share (%)</th>
                <th>Strategic Corrective Action</th>
              </tr>
            </thead>
            <tbody>
              {rcaLeaderboard.map((item) => (
                <tr key={item.rank}>
                  <td style={{ fontWeight: '700', color: item.rank === 1 ? '#ef4444' : (item.rank === 2 ? '#f97316' : 'var(--text-primary)') }}>
                    #{item.rank}
                  </td>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                    {item.root_cause}
                  </td>
                  <td>
                    <span className="badge" style={{ backgroundColor: 'rgba(6, 182, 212, 0.1)', color: '#38bdf8' }}>
                      {item.primary_application}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {item.category}
                  </td>
                  <td style={{ fontWeight: '700', fontFamily: 'var(--font-mono)' }}>
                    {item.occurrences}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: '600' }}>{item.percentage}</span>
                      <div style={{ width: '50px', height: '4px', backgroundColor: 'var(--bg-elevated)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ width: item.percentage, height: '100%', backgroundColor: '#6366f1' }} />
                      </div>
                    </div>
                  </td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {item.action}
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
