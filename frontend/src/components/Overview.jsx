import React from 'react';
import { Share2, Clock, Play, Pause, AlertTriangle } from 'lucide-react';

export default function Overview({ status, schedules, logs, setActiveTab }) {
  const publishedCount = logs.filter(l => l.status === 'completed').length;
  const pendingSchedules = schedules.filter(s => s.status === 'pending');
  const pausedSchedules = schedules.filter(s => s.status === 'paused');
  const failedCount = logs.filter(l => l.status === 'failed').length;

  const nextSchedule = pendingSchedules.length > 0 ? pendingSchedules[0] : null;

  const formatDate = (isoStr) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoStr;
    }
  };

  return (
    <div>
      <div className="overview-header">
        <h2 style={{ fontSize: '32px', marginBottom: '8px' }}>Dashboard Overview</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Welcome to your autonomous LinkedIn poster center.</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ background: 'rgba(0, 119, 181, 0.15)', color: 'var(--accent-linkedin)' }}>
            <Share2 size={24} />
          </div>
          <div>
            <div className="stat-value">{publishedCount}</div>
            <div className="stat-label">Total Shared</div>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)' }}>
            <Clock size={24} />
          </div>
          <div>
            <div className="stat-value">{pendingSchedules.length}</div>
            <div className="stat-label">Pending Runs</div>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ background: 'rgba(148, 163, 184, 0.15)', color: 'var(--text-secondary)' }}>
            <Pause size={24} />
          </div>
          <div>
            <div className="stat-value">{pausedSchedules.length}</div>
            <div className="stat-label">Paused Schedules</div>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)' }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <div className="stat-value">{failedCount}</div>
            <div className="stat-label">Failed Runs</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Next Scheduled Action */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>Next Planned Action</h3>
          {nextSchedule ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
              <div>
                <span className="status-pill pending" style={{ marginBottom: '8px' }}>Pending Publication</span>
                <h4 style={{ fontSize: '18px', color: 'var(--text-primary)' }}>Topic: {nextSchedule.topic}</h4>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Scheduled for: <strong>{formatDate(nextSchedule.scheduled_time)}</strong>
                </p>
              </div>

              <div style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid var(--glass-border)',
                borderRadius: '10px',
                padding: '16px',
                fontSize: '13px',
                lineHeight: '1.6',
                color: 'var(--text-secondary)',
                maxHeight: '150px',
                overflowY: 'auto'
              }}>
                {nextSchedule.commentary}
              </div>

              <div style={{ marginTop: 'auto', display: 'flex', gap: '10px' }}>
                <button 
                  onClick={() => setActiveTab('scheduler')}
                  style={{
                    padding: '10px 16px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: 'var(--text-primary)',
                    fontSize: '13px'
                  }}
                >
                  Edit in Planner
                </button>
              </div>
            </div>
          ) : (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px 20px',
              textAlign: 'center',
              color: 'var(--text-secondary)',
              flex: 1,
              gap: '12px'
            }}>
              <p>No upcoming schedules planned.</p>
              <button 
                onClick={() => setActiveTab('scheduler')}
                style={{
                  padding: '10px 18px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #0077b5 0%, #00a0dc 100%)',
                  color: 'white',
                  fontSize: '13px',
                  fontWeight: '600'
                }}
              >
                Plan a Schedule
              </button>
            </div>
          )}
        </div>

        {/* Integration Status Panel */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '20px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>System Integrations</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0' }}>
              <div>
                <h4 style={{ fontSize: '15px' }}>LinkedIn Account</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {status.linkedin_connected ? `Connected as: ${status.linkedin_member_name}` : 'Not connected'}
                </p>
              </div>
              <span className={`status-pill ${status.linkedin_connected ? 'completed' : 'failed'}`}>
                {status.linkedin_connected ? 'Connected' : 'Offline'}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderTop: '1px solid rgba(255, 255, 255, 0.03)' }}>
              <div>
                <h4 style={{ fontSize: '15px' }}>Gemini AI Engine</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {status.gemini_configured ? 'API key active' : 'API key not configured (Using local templates)'}
                </p>
              </div>
              <span className={`status-pill ${status.gemini_configured ? 'completed' : 'paused'}`}>
                {status.gemini_configured ? 'Enabled' : 'Template Mode'}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderTop: '1px solid rgba(255, 255, 255, 0.03)' }}>
              <div>
                <h4 style={{ fontSize: '15px' }}>Background Scheduler</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Checked every 15s locally</p>
              </div>
              <span className="status-pill completed">Active</span>
            </div>

            {!status.linkedin_connected && (
              <div style={{
                marginTop: 'auto',
                padding: '12px',
                borderRadius: '8px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                fontSize: '12px',
                color: '#fca5a5',
                lineHeight: '1.5'
              }}>
                ⚠️ <strong>LinkedIn Connection Required:</strong> To enable automated sharing, go to Settings, enter your client credentials, and click authorize.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
