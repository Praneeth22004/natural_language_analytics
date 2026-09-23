import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Sparkles, 
  Calendar, 
  FileSpreadsheet, 
  FileType, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { generateExecutiveReport } from '../api';
import MarkdownRenderer from '../components/MarkdownRenderer';

const SAMPLE_PERIODS = [
  'Last 30 Days Enterprise Availability Report',
  'March 2026 Incident Performance Review',
  'Past 6 Months Operations Summary',
  'Q1 2026 Quarterly Operations Summary',
  'All-Time Enterprise Availability Report',
  'August 2026 Incident Performance Review'
];

export default function ExecutiveReportsPage() {
  const [period, setPeriod] = useState('Last 30 Days Enterprise Availability Report');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exportingFormat, setExportingFormat] = useState(null);

  const handleGenerate = async (selectedPeriod = period) => {
    setLoading(true);
    try {
      const data = await generateExecutiveReport(selectedPeriod);
      setReport(data);
    } catch (err) {
      alert(`Error generating report: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleGenerate('Last 30 Days Enterprise Availability Report');
  }, []);

  const handleExport = async (format) => {
    if (!report) return;
    setExportingFormat(format);
    try {
      const response = await fetch(`http://localhost:8000/api/reports/export/${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report)
      });
      if (!response.ok) throw new Error('Export failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ServiceNow_Executive_Report_${format.toUpperCase()}_${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Export error: ${err.message}`);
    } finally {
      setExportingFormat(null);
    }
  };

  const kpis = report?.kpis || {};
  const totalIncidents = kpis.total_incidents ?? 0;

  return (
    <div className="page-body">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h2 style={{ fontSize: '22px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={24} color="#6366f1" />
            Executive Incident Reporting & Compliance
          </h2>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            AI-compiled operational briefs, SLA scorecards, and multi-format document export from live ServiceNow dev204434
          </span>
        </div>

        {/* Export Buttons */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn-secondary"
            onClick={() => handleExport('pdf')}
            disabled={!report || exportingFormat !== null}
            style={{ fontSize: '12px' }}
          >
            <FileType size={15} color="#ef4444" />
            <span>{exportingFormat === 'pdf' ? 'Exporting...' : 'Export PDF'}</span>
          </button>
          <button
            className="btn-secondary"
            onClick={() => handleExport('docx')}
            disabled={!report || exportingFormat !== null}
            style={{ fontSize: '12px' }}
          >
            <FileText size={15} color="#3b82f6" />
            <span>{exportingFormat === 'docx' ? 'Exporting...' : 'Export Word'}</span>
          </button>
          <button
            className="btn-secondary"
            onClick={() => handleExport('xlsx')}
            disabled={!report || exportingFormat !== null}
            style={{ fontSize: '12px' }}
          >
            <FileSpreadsheet size={15} color="#10b981" />
            <span>{exportingFormat === 'xlsx' ? 'Exporting...' : 'Export Excel'}</span>
          </button>
        </div>
      </div>

      {/* Period Selector & Generation Bar */}
      <div className="glass-card" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <Calendar size={16} color="var(--text-muted)" />
            <span style={{ fontSize: '13px', fontWeight: '600' }}>Report Period:</span>
            {SAMPLE_PERIODS.map((p) => (
              <button
                key={p}
                onClick={() => {
                  setPeriod(p);
                  handleGenerate(p);
                }}
                className={`badge ${period === p ? 'badge-simulation' : ''}`}
                style={{
                  cursor: 'pointer',
                  padding: '6px 12px',
                  background: period === p ? 'rgba(6, 182, 212, 0.2)' : 'var(--bg-elevated)',
                  border: period === p ? '1px solid #06b6d4' : '1px solid var(--border-subtle)',
                  color: period === p ? '#38bdf8' : 'var(--text-secondary)',
                  fontWeight: period === p ? '700' : '500'
                }}
              >
                {p}
              </button>
            ))}
          </div>

          <button
            className="btn-primary"
            onClick={() => handleGenerate(period)}
            disabled={loading}
            style={{ padding: '8px 18px', fontSize: '13px' }}
          >
            <Sparkles size={15} />
            <span>{loading ? 'Compiling...' : 'Regenerate Report'}</span>
          </button>
        </div>
      </div>

      {loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ display: 'inline-block', width: '24px', height: '24px', border: '2px solid #6366f1', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Aggregating KPIs, recurring patterns, and executive narrative from ServiceNow...</div>
        </div>
      )}

      {/* Report Document Preview */}
      {!loading && report && (
        <div className="glass-card" style={{ padding: '36px', maxWidth: '1000px', margin: '0 auto', background: 'rgba(17, 24, 39, 0.9)' }}>
          {/* Document Title Header */}
          <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '20px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="badge badge-live">Verified ServiceNow Telemetry</span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Generated: {report.generated_at}
              </span>
            </div>
            <h2 style={{ fontSize: '26px', fontWeight: '800', marginTop: '10px' }}>
              {report.period}
            </h2>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Prepared by: Enterprise Natural Language Incident Intelligence Layer (dev204434)
            </span>
          </div>

          {/* Zero Incident Notice if applicable */}
          {totalIncidents === 0 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'rgba(59, 130, 246, 0.08)',
              border: '1px solid rgba(59, 130, 246, 0.22)',
              borderRadius: '8px',
              padding: '12px 16px',
              marginBottom: '24px',
              color: 'var(--text-secondary)',
              fontSize: '13px'
            }}>
              <AlertCircle size={16} color="#38bdf8" />
              <span>
                ServiceNow instance <strong>dev204434</strong> recorded <strong>0 incidents</strong> for <strong>{report.period}</strong>. Showing verified live zero-state scorecard.
              </span>
            </div>
          )}

          {/* Executive Summary */}
          <div style={{ marginBottom: '28px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)', marginBottom: '10px' }}>
              1. Executive Summary
            </h3>
            <div style={{ fontSize: '14px', lineHeight: '1.8', color: 'var(--text-primary)', background: 'var(--bg-elevated)', padding: '16px 20px', borderRadius: '8px' }}>
              <MarkdownRenderer content={report.executive_summary} />
            </div>
          </div>

          {/* Key Metrics Scorecard */}
          <div style={{ marginBottom: '28px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)', marginBottom: '14px' }}>
              2. Key Operational Scorecard
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
              <div style={{ padding: '14px', background: 'var(--bg-elevated)', borderRadius: '8px', textAlign: 'center' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Incidents</span>
                <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--text-primary)', marginTop: '4px' }}>
                  {totalIncidents}
                </div>
              </div>
              <div style={{ padding: '14px', background: 'var(--bg-elevated)', borderRadius: '8px', textAlign: 'center' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>P1 Critical</span>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#f87171', marginTop: '4px' }}>
                  {kpis.critical_incidents ?? 0}
                </div>
              </div>
              <div style={{ padding: '14px', background: 'var(--bg-elevated)', borderRadius: '8px', textAlign: 'center' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>SLA Compliance</span>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#34d399', marginTop: '4px' }}>
                  {kpis.sla_compliance_rate ?? 100}%
                </div>
              </div>
              <div style={{ padding: '14px', background: 'var(--bg-elevated)', borderRadius: '8px', textAlign: 'center' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>MTTR Average</span>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#38bdf8', marginTop: '4px' }}>
                  {totalIncidents > 0 && kpis.mttr_hours ? `${kpis.mttr_hours}h` : '0.0h'}
                </div>
              </div>
            </div>
          </div>

          {/* Top Affected Applications Table */}
          <div style={{ marginBottom: '28px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)', marginBottom: '12px' }}>
              3. Service Impact Distribution
            </h3>
            <table className="enterprise-table">
              <thead>
                <tr>
                  <th>Application / CI</th>
                  <th>Total Tickets</th>
                  <th>P1 Critical</th>
                  <th>P2 High</th>
                  <th>SLA Breached</th>
                </tr>
              </thead>
              <tbody>
                {(report.top_affected_applications || []).length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '28px', color: 'var(--text-muted)', fontSize: '13px' }}>
                      No affected configuration items or incidents recorded in ServiceNow for {report.period}.
                    </td>
                  </tr>
                ) : (
                  (report.top_affected_applications || []).map((app, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: '600' }}>{app.name}</td>
                      <td>{app.total}</td>
                      <td style={{ color: app.p1 > 0 ? '#ef4444' : 'var(--text-secondary)' }}>{app.p1}</td>
                      <td style={{ color: app.p2 > 0 ? '#f97316' : 'var(--text-secondary)' }}>{app.p2}</td>
                      <td>{app.sla_breached > 0 ? `${app.sla_breached} missed` : 'None'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Strategic Corrective Actions */}
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)', marginBottom: '12px' }}>
              4. Strategic Corrective Actions & Prevention Roadmap
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(report.strategic_recommendations || []).map((rec, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px', color: 'var(--text-primary)' }}>
                  <CheckCircle2 size={16} color="#10b981" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
