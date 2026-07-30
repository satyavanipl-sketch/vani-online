import React, { useState } from 'react';
import { Trash2, Terminal, RefreshCw } from 'lucide-react';
import { clearLogs } from '../utils/api';

export default function Logs({ logs, refreshData }) {
  const [isClearing, setIsClearing] = useState(false);

  const handleClear = async () => {
    if (!confirm('Are you sure you want to clear all history logs?')) return;
    setIsClearing(true);
    try {
      await clearLogs();
      refreshData();
    } catch (e) {
      alert(e.message || 'Failed to clear logs.');
    } finally {
      setIsClearing(false);
    }
  };

  const formatDate = (isoStr) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString([], { hour12: false });
    } catch {
      return isoStr;
    }
  };

  return (
    <div>
      <div className="overview-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h2 style={{ fontSize: '32px', marginBottom: '8px' }}>Execution Logs</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Track automated background actions and publication outputs.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={refreshData}
            style={{
              padding: '10px 16px',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--glass-border)',
              color: 'var(--text-primary)',
              fontSize: '13px'
            }}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          
          <button 
            onClick={handleClear}
            disabled={isClearing || logs.length === 0}
            style={{
              padding: '10px 16px',
              borderRadius: '10px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              color: '#fca5a5',
              fontSize: '13px',
              opacity: (isClearing || logs.length === 0) ? 0.5 : 1
            }}
          >
            <Trash2 size={14} />
            Clear History
          </button>
        </div>
      </div>

      <div className="glass-panel">
        <h3 style={{ fontSize: '18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Terminal size={18} style={{ color: '#38bdf8' }} />
          System Console Output
        </h3>

        <div className="terminal-view">
          <div className="terminal-line success">
            [SYSINFO] System active. Listening for events...
          </div>
          
          {logs.length > 0 ? (
            logs.map((log) => {
              const isError = log.status === 'failed';
              return (
                <div key={log.id} style={{ marginBottom: '14px', borderBottom: '1px solid rgba(255, 255, 255, 0.02)', paddingBottom: '10px' }}>
                  <div className="terminal-line" style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    <span className="terminal-line timestamp">[{formatDate(log.timestamp)}]</span>
                    <span style={{ color: '#e2e8f0', fontWeight: 'bold' }}>Topic: {log.topic}</span>
                    <span className={`status-pill ${log.status}`} style={{ padding: '2px 8px', fontSize: '10px' }}>
                      {log.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="terminal-line" style={{ color: 'var(--text-secondary)', paddingLeft: '20px', margin: '6px 0', wordBreak: 'break-word', fontSize: '12px' }}>
                    {log.commentary}
                  </div>

                  {isError ? (
                    <div className="terminal-line error" style={{ paddingLeft: '20px', fontSize: '12px' }}>
                      ↳ ❌ Error: {log.error_message}
                    </div>
                  ) : (
                    <div className="terminal-line success" style={{ paddingLeft: '20px', fontSize: '12px' }}>
                      ↳ 🚀 Published Post URN: {log.published_urn}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div style={{
              padding: '60px 0',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontFamily: 'monospace'
            }}>
              --- No execution logs recorded yet. Run a post or wait for scheduled runs to appear here. ---
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
