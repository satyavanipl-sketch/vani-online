import React, { useState } from 'react';
import { Calendar, Trash2, Edit2, Play, Pause, AlertCircle, Save, X, RefreshCw } from 'lucide-react';
import { createSchedule, updateSchedule, toggleSchedule, deleteSchedule } from '../utils/api';

const PRESETS = [
  'Clean Code',
  'Energy Management',
  'Technical Debt',
  'AI Augmented Engineering',
  'System Design & Scalability',
  'Developer Burnout',
  'Microservices Architecture'
];

export default function Scheduler({ schedules, refreshData }) {
  const [topic, setTopic] = useState(PRESETS[0]);
  const [customTopic, setCustomTopic] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  // Editing state
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [editCommentary, setEditCommentary] = useState('');
  const [editCardText, setEditCardText] = useState('');
  const [editTime, setEditTime] = useState('');

  const activeTopic = topic === 'Custom' ? customTopic : topic;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!scheduledTime) {
      setError('Please select a scheduled date and time.');
      return;
    }
    if (topic === 'Custom' && !customTopic.trim()) {
      setError('Please specify a custom topic.');
      return;
    }

    // Check if date is in the future
    const selectedDate = new Date(scheduledTime);
    if (selectedDate <= new Date()) {
      setError('Scheduled time must be in the future.');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await createSchedule(activeTopic, selectedDate.toISOString());
      setScheduledTime('');
      setCustomTopic('');
      refreshData();
    } catch (e) {
      setError(e.message || 'Failed to create schedule.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggle = async (id) => {
    try {
      await toggleSchedule(id);
      refreshData();
    } catch (e) {
      setError(e.message || 'Failed to toggle schedule state.');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    try {
      await deleteSchedule(id);
      refreshData();
    } catch (e) {
      setError(e.message || 'Failed to delete schedule.');
    }
  };

  const startEdit = (s) => {
    setEditingSchedule(s);
    setEditCommentary(s.commentary);
    setEditCardText(s.card_text);
    
    // Format ISO date back to local datetime-local format (YYYY-MM-DDTHH:MM)
    try {
      const date = new Date(s.scheduled_time);
      const tzoffset = date.getTimezoneOffset() * 60000; // offset in milliseconds
      const localISOTime = (new Date(date - tzoffset)).toISOString().slice(0, 16);
      setEditTime(localISOTime);
    } catch {
      setEditTime(s.scheduled_time);
    }
  };

  const saveEdit = async () => {
    if (!editingSchedule) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const selectedDate = new Date(editTime);
      await updateSchedule(editingSchedule.id, selectedDate.toISOString(), editCommentary, editCardText);
      setEditingSchedule(null);
      refreshData();
    } catch (e) {
      setError(e.message || 'Failed to save edit.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDate = (isoStr) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoStr;
    }
  };

  return (
    <div>
      <div className="overview-header">
        <h2 style={{ fontSize: '32px', marginBottom: '8px' }}>Scheduler Planner</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Configure automated, timed releases and manage planned content streams.</p>
      </div>

      {error && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '16px',
          borderRadius: '12px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          color: '#f87171',
          marginBottom: '24px',
          fontSize: '14px'
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="grid-2" style={{ alignItems: 'start' }}>
        
        {/* Create Schedule Form */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={18} style={{ color: 'var(--accent-linkedin)' }} />
            Plan New Publication
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Topic Category</label>
              <select value={topic} onChange={(e) => setTopic(e.target.value)} style={{ width: '100%' }}>
                {PRESETS.map((t, idx) => (
                  <option key={idx} value={t}>{t}</option>
                ))}
                <option value="Custom">-- Custom Topic --</option>
              </select>
            </div>

            {topic === 'Custom' && (
              <div className="form-group">
                <label>Custom Topic Title</label>
                <input 
                  type="text" 
                  placeholder="e.g. Modern Web Tech"
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label>Release Date & Time</label>
              <input 
                type="datetime-local" 
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                style={{ width: '100%' }}
                required
              />
            </div>

            <button 
              type="submit" 
              disabled={isSubmitting}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #0077b5 0%, #00a0dc 100%)',
                color: 'white',
                fontWeight: '600',
                marginTop: '10px',
                opacity: isSubmitting ? 0.6 : 1
              }}
            >
              {isSubmitting ? <RefreshCw className="animate-spin" size={18} /> : 'Generate & Schedule'}
            </button>
          </form>
        </div>

        {/* Edit Modal (Shows when editing is active) */}
        {editingSchedule && (
          <div className="glass-panel" style={{ border: '1px solid var(--accent-linkedin)' }}>
            <h3 style={{ fontSize: '18px', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>✏️ Edit Scheduled Post</span>
              <button onClick={() => setEditingSchedule(null)} style={{ background: 'transparent', color: 'var(--text-muted)' }}>
                <X size={18} />
              </button>
            </h3>
            
            <div className="form-group">
              <label>Scheduled Release Time</label>
              <input 
                type="datetime-local" 
                value={editTime}
                onChange={(e) => setEditTime(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div className="form-group">
              <label>LinkedIn Commentary Text</label>
              <textarea 
                value={editCommentary}
                onChange={(e) => setEditCommentary(e.target.value)}
                style={{ width: '100%', minHeight: '120px', resize: 'vertical' }}
              />
            </div>

            <div className="form-group">
              <label>Visual Card Text</label>
              <input 
                type="text" 
                maxLength={50}
                value={editCardText}
                onChange={(e) => setEditCardText(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              <button 
                onClick={() => setEditingSchedule(null)}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: 'var(--text-primary)'
                }}
              >
                Cancel
              </button>
              <button 
                onClick={saveEdit}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  background: 'var(--accent-linkedin)',
                  color: 'white',
                  fontWeight: '600'
                }}
              >
                <Save size={16} />
                Save Changes
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Planned Streams Queue */}
      <div className="glass-panel" style={{ marginTop: '40px' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>
          Planned Streams Queue
        </h3>
        
        {schedules.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Topic</th>
                  <th>Scheduled Time</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: '500' }}>{s.topic}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{formatDate(s.scheduled_time)}</td>
                    <td>
                      <span className={`status-pill ${s.status}`}>
                        {s.status.charAt(0).toUpperCase() + s.status.slice(1)}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '8px' }}>
                        
                        {s.status === 'pending' && (
                          <button 
                            onClick={() => handleToggle(s.id)}
                            title="Pause"
                            style={{
                              padding: '6px',
                              borderRadius: '6px',
                              background: 'rgba(255, 255, 255, 0.03)',
                              color: 'var(--text-secondary)'
                            }}
                          >
                            <Pause size={14} />
                          </button>
                        )}

                        {s.status === 'paused' && (
                          <button 
                            onClick={() => handleToggle(s.id)}
                            title="Resume"
                            style={{
                              padding: '6px',
                              borderRadius: '6px',
                              background: 'rgba(16, 185, 129, 0.1)',
                              color: 'var(--accent-green)'
                            }}
                          >
                            <Play size={14} />
                          </button>
                        )}

                        <button 
                          onClick={() => startEdit(s)}
                          title="Edit"
                          style={{
                            padding: '6px',
                            borderRadius: '6px',
                            background: 'rgba(255, 255, 255, 0.03)',
                            color: 'var(--text-secondary)'
                          }}
                        >
                          <Edit2 size={14} />
                        </button>

                        <button 
                          onClick={() => handleDelete(s.id)}
                          title="Delete"
                          style={{
                            padding: '6px',
                            borderRadius: '6px',
                            background: 'rgba(239, 68, 68, 0.05)',
                            color: 'var(--accent-red)'
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{
            padding: '40px 0',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '14px'
          }}>
            No scheduled actions configured. Set your parameters above to schedule your first post.
          </div>
        )}
      </div>
    </div>
  );
}
