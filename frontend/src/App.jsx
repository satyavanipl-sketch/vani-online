import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Sparkles, Calendar, Settings as SettingsIcon, Terminal, Link2, HelpCircle } from 'lucide-react';
import { getStatus, getSchedules, getLogs } from './utils/api';
import Overview from './components/Overview';
import AdhocCreator from './components/AdhocCreator';
import Scheduler from './components/Scheduler';
import Settings from './components/Settings';
import Logs from './components/Logs';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [status, setStatus] = useState({
    linkedin_connected: false,
    linkedin_member_name: '',
    linkedin_person_urn: '',
    gemini_configured: false,
    client_id_configured: false,
    client_secret_configured: false,
    active_schedules_count: 0
  });
  const [schedules, setSchedules] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refreshData = async () => {
    try {
      const [statusRes, schedulesRes, logsRes] = await Promise.all([
        getStatus(),
        getSchedules(),
        getLogs()
      ]);
      setStatus(statusRes);
      // Sort schedules: pending/paused first, then completed/failed
      const sortedSchedules = [...schedulesRes].sort((a, b) => {
        if (a.status === 'pending' && b.status !== 'pending') return -1;
        if (a.status !== 'pending' && b.status === 'pending') return 1;
        return new Date(a.scheduled_time) - new Date(b.scheduled_time);
      });
      setSchedules(sortedSchedules);
      setLogs(logsRes);
      setError(null);
    } catch (e) {
      console.error(e);
      setError('Connection to backend API failed. Make sure the FastAPI server is running on port 8002.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    // Poll data every 10 seconds for reactive status / auto-completed schedules
    const interval = setInterval(refreshData, 10000);
    return () => clearInterval(interval);
  }, []);

  // Check for successful authentication in the URL parameters
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth') === 'success') {
      // Clear query params to make URL clean
      window.history.replaceState({}, document.title, window.location.pathname);
      refreshData();
    }
  }, []);

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':
        return <Overview status={status} schedules={schedules} logs={logs} setActiveTab={setActiveTab} />;
      case 'creator':
        return <AdhocCreator refreshData={refreshData} />;
      case 'scheduler':
        return <Scheduler schedules={schedules} refreshData={refreshData} />;
      case 'settings':
        return <Settings status={status} refreshData={refreshData} />;
      case 'logs':
        return <Logs logs={logs} refreshData={refreshData} />;
      default:
        return <Overview status={status} schedules={schedules} logs={logs} setActiveTab={setActiveTab} />;
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        gap: '20px',
        background: 'radial-gradient(circle at top left, #0e1e35 0%, #03080e 100%)',
        color: 'white'
      }}>
        <div className="stat-icon" style={{
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: 'rgba(0, 119, 181, 0.1)',
          color: 'var(--accent-linkedin)',
          animation: 'pulse-glow 1.5s infinite ease-in-out'
        }}>
          <Link2 size={32} />
        </div>
        <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: '500' }}>Starting Autoposter Hub...</h3>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <nav className="sidebar">
        <div className="logo-container">
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #0077b5 0%, #00a0dc 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '18px',
            fontFamily: 'var(--font-display)'
          }}>
            in
          </div>
          <span className="logo-text">autoposter.ai</span>
        </div>

        <ul className="nav-links">
          <li className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}>
            <button onClick={() => setActiveTab('overview')}>
              <LayoutDashboard size={18} />
              Overview
            </button>
          </li>
          <li className={`nav-item ${activeTab === 'creator' ? 'active' : ''}`}>
            <button onClick={() => setActiveTab('creator')}>
              <Sparkles size={18} />
              Ad-hoc Creator
            </button>
          </li>
          <li className={`nav-item ${activeTab === 'scheduler' ? 'active' : ''}`}>
            <button onClick={() => setActiveTab('scheduler')}>
              <Calendar size={18} />
              Scheduler Planner
            </button>
          </li>
          <li className={`nav-item ${activeTab === 'logs' ? 'active' : ''}`}>
            <button onClick={() => setActiveTab('logs')}>
              <Terminal size={18} />
              Execution Logs
            </button>
          </li>
          <li className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}>
            <button onClick={() => setActiveTab('settings')}>
              <SettingsIcon size={18} />
              Settings
            </button>
          </li>
        </ul>

        {/* Sidebar Footer Account Status */}
        <div className="sidebar-footer">
          <div className="profile-widget">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: status.linkedin_connected ? 'var(--accent-green)' : 'var(--accent-red)',
                boxShadow: status.linkedin_connected ? '0 0 8px var(--accent-green)' : '0 0 8px var(--accent-red)'
              }} />
              <span style={{ fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                LinkedIn Connection
              </span>
            </div>
            <span style={{ fontSize: '13px', fontWeight: '500', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--text-primary)' }}>
              {status.linkedin_connected ? status.linkedin_member_name : 'Account Disconnected'}
            </span>
          </div>
        </div>
      </nav>

      {/* Main Page Content */}
      <main className="main-content">
        {error && (
          <div style={{
            padding: '16px',
            borderRadius: '12px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            color: '#f87171',
            marginBottom: '30px',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <HelpCircle size={20} />
            <div>
              <strong>Connectivity Alert:</strong> {error}
            </div>
          </div>
        )}

        {renderActiveTab()}
      </main>
    </div>
  );
}
