import React, { useState, useEffect } from 'react';
import { X, Sparkles, AlertCircle, CheckCircle2, Clock, Server, User, Tag, MessageSquare, Send, RefreshCw, FileText, Check } from 'lucide-react';
import { summarizeIncident, fetchIncidentWorkNotes, addIncidentWorkNote } from '../api';

export default function IncidentDetailModal({ isOpen, onClose, incident }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [loadingAi, setLoadingAi] = useState(false);
  const [postMortem, setPostMortem] = useState(null);

  // Work notes state
  const [workNotes, setWorkNotes] = useState([]);
  const [loadingNotes, setLoadingNotes] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [submittingNote, setSubmittingNote] = useState(false);
  const [noteSuccess, setNoteSuccess] = useState('');
  const [noteError, setNoteError] = useState('');

  const targetIdentifier = incident?.number || incident?.sys_id;

  // Load work notes whenever modal opens or incident changes
  useEffect(() => {
    if (isOpen && targetIdentifier) {
      loadWorkNotes();
      setPostMortem(null);
      setNoteSuccess('');
      setNoteError('');
      setNewNote('');
    }
  }, [isOpen, targetIdentifier]);

  const loadWorkNotes = async () => {
    if (!targetIdentifier) return;
    setLoadingNotes(true);
    try {
      const res = await fetchIncidentWorkNotes(targetIdentifier);
      setWorkNotes(res.work_notes || []);
    } catch (err) {
      console.warn('Could not load work notes:', err);
    } finally {
      setLoadingNotes(false);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim() || submittingNote) return;

    setSubmittingNote(true);
    setNoteSuccess('');
    setNoteError('');

    try {
      const res = await addIncidentWorkNote(targetIdentifier, newNote.trim());
      if (res.updated_notes && res.updated_notes.length > 0) {
        setWorkNotes(res.updated_notes);
      } else {
        // Optimistically prepend note if list wasn't returned
        const optimisticEntry = {
          type: 'work_notes',
          value: newNote.trim(),
          created_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
          created_by: 'Current User'
        };
        setWorkNotes(prev => [optimisticEntry, ...prev]);
      }
      setNewNote('');
      setNoteSuccess('Work note successfully appended and synced to ServiceNow!');
      setTimeout(() => setNoteSuccess(''), 4500);
    } catch (err) {
      setNoteError(err.message || 'Failed to submit work note');
    } finally {
      setSubmittingNote(false);
    }
  };

  if (!isOpen || !incident) return null;

  const handleGeneratePostMortem = async () => {
    setLoadingAi(true);
    try {
      const res = await summarizeIncident(targetIdentifier);
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
      4: { label: 'P4 - Low', cls: 'badge-p4' },
      5: { label: 'P5 - Planning', cls: 'badge-p5' }
    };
    const item = map[p] || { label: `P${p}`, cls: 'badge-p3' };
    return <span className={`badge ${item.cls}`}>{item.label}</span>;
  };

  const isClosed = ['Closed', 'Resolved', '7', '8'].includes(String(incident.state));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '820px' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
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
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          padding: '14px 16px',
          backgroundColor: 'var(--bg-elevated)',
          borderRadius: '10px',
          marginBottom: '18px',
          fontSize: '13px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={15} color="#06b6d4" />
            <span style={{ color: 'var(--text-muted)' }}>CI:</span>
            <span style={{ fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {incident.cmdb_ci || 'General IT'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tag size={15} color="#818cf8" />
            <span style={{ color: 'var(--text-muted)' }}>Group:</span>
            <span style={{ fontWeight: '600' }}>{incident.assignment_group || 'Service Desk'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <User size={15} color="#10b981" />
            <span style={{ color: 'var(--text-muted)' }}>Assignee:</span>
            <span style={{ fontWeight: '600' }}>{incident.assigned_to || 'Unassigned'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={15} color="#f59e0b" />
            <span style={{ color: 'var(--text-muted)' }}>Opened:</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
              {incident.opened_at ? incident.opened_at.replace('T', ' ').slice(0, 16) : 'N/A'}
            </span>
          </div>
        </div>

        {/* Modal Navigation Tabs */}
        <div className="modal-tabs">
          <button
            type="button"
            className={`modal-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Sparkles size={15} />
            <span>Overview & AI RCA</span>
          </button>
          <button
            type="button"
            className={`modal-tab-btn ${activeTab === 'worknotes' ? 'active' : ''}`}
            onClick={() => setActiveTab('worknotes')}
          >
            <MessageSquare size={15} />
            <span>Work Notes & Activity</span>
            <span style={{
              fontSize: '11px',
              padding: '2px 7px',
              borderRadius: '999px',
              backgroundColor: activeTab === 'worknotes' ? 'var(--accent-primary)' : 'var(--bg-elevated)',
              color: '#ffffff',
              fontWeight: '700'
            }}>
              {workNotes.length}
            </span>
          </button>
        </div>

        {/* TAB 1: Overview & AI Post-Mortem */}
        {activeTab === 'overview' && (
          <div>
            {/* Description */}
            <div style={{ marginBottom: '20px' }}>
              <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Technical Description
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
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '18px' }}>
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
        )}

        {/* TAB 2: Work Notes & Journal Stream */}
        {activeTab === 'worknotes' && (
          <div className="work-notes-container">
            {/* Add Work Note Input Card */}
            <div className="work-note-input-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '13px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MessageSquare size={15} color="var(--accent-primary)" />
                  Add Internal Work Note
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Appends to live ServiceNow journal
                </span>
              </div>

              <form onSubmit={handleAddNote} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <textarea
                  className="work-note-textarea"
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Record diagnostic observations, mitigation steps, or on-call communication regarding this ticket..."
                  disabled={submittingNote}
                  rows={3}
                />

                {noteSuccess && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: '#34d399',
                    fontSize: '12px'
                  }}>
                    <Check size={14} />
                    <span>{noteSuccess}</span>
                  </div>
                )}

                {noteError && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(239, 68, 68, 0.12)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#f87171',
                    fontSize: '12px'
                  }}>
                    <AlertCircle size={14} />
                    <span>{noteError}</span>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '10px' }}>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={!newNote.trim() || submittingNote}
                    style={{
                      fontSize: '12px',
                      padding: '8px 16px',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <Send size={13} />
                    <span>{submittingNote ? 'Saving to ServiceNow...' : 'Append Work Note'}</span>
                  </button>
                </div>
              </form>
            </div>

            {/* Work Notes Stream Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)' }}>
                  Activity & Journal History
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  ({workNotes.length} {workNotes.length === 1 ? 'entry' : 'entries'})
                </span>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={loadWorkNotes}
                disabled={loadingNotes}
                style={{ padding: '4px 10px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                title="Refresh work notes from ServiceNow"
              >
                <RefreshCw size={12} className={loadingNotes ? 'spin-icon' : ''} />
                <span>Sync Notes</span>
              </button>
            </div>

            {/* Loading Indicator */}
            {loadingNotes && (
              <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '13px' }}>
                <div style={{ display: 'inline-block', width: '18px', height: '18px', border: '2px solid #6366f1', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', marginRight: '8px' }} />
                Fetching work notes from ServiceNow...
              </div>
            )}

            {/* Empty State */}
            {!loadingNotes && workNotes.length === 0 && (
              <div style={{
                textAlign: 'center',
                padding: '36px 20px',
                backgroundColor: 'rgba(0,0,0,0.15)',
                borderRadius: '8px',
                border: '1px dashed var(--border-subtle)',
                color: 'var(--text-muted)',
                fontSize: '13px'
              }}>
                <FileText size={24} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <p>No prior work notes or journal entries found on this incident.</p>
                <p style={{ fontSize: '12px', marginTop: '4px' }}>Use the box above to log the first diagnostic update.</p>
              </div>
            )}

            {/* Chronological List of Work Notes */}
            {!loadingNotes && workNotes.length > 0 && (
              <div className="work-notes-timeline">
                {workNotes.map((note, idx) => (
                  <div
                    key={note.sys_id || idx}
                    className={`work-note-entry ${note.type === 'comments' ? 'comments' : ''}`}
                  >
                    <div className="work-note-header">
                      <div className="work-note-author">
                        <User size={13} color="var(--accent-primary)" />
                        <span>{note.created_by || 'System'}</span>
                        <span
                          className="badge"
                          style={{
                            fontSize: '10px',
                            padding: '1px 6px',
                            backgroundColor: note.type === 'comments' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                            color: note.type === 'comments' ? '#38bdf8' : '#a5b4fc',
                            border: '1px solid rgba(99, 102, 241, 0.25)'
                          }}
                        >
                          {note.type === 'comments' ? 'Customer Comment' : 'Work Note'}
                        </span>
                      </div>
                      <div className="work-note-time">
                        <Clock size={11} style={{ display: 'inline', marginRight: '4px', verticalAlign: '-1px' }} />
                        {note.created_at || 'Just now'}
                      </div>
                    </div>
                    <div className="work-note-text">
                      {note.value}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
