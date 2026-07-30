import React, { useState, useEffect } from 'react';
import { Save, Key, Link2, LogOut, CheckCircle, Copy, ClipboardCheck, Info } from 'lucide-react';
import { saveConfig, getAuthUrl, logout } from '../utils/api';

export default function Settings({ status, refreshData }) {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [personUrn, setPersonUrn] = useState('');
  const [memberName, setMemberName] = useState('');
  
  // OAuth settings
  const [scopeMode, setScopeMode] = useState('minimal'); // Default to minimal/share-only since openid is often not authorized
  const [isSaving, setIsSaving] = useState(false);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const redirectUri = 'http://localhost:8002/api/callback';

  // Load status values if available
  useEffect(() => {
    if (status) {
      setPersonUrn(status.linkedin_person_urn || '');
      setMemberName(status.linkedin_member_name || '');
    }
  }, [status]);

  // Check URL parameters for redirection notifications
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('need_urn') === 'true') {
      setMessage('Authenticated successfully! Since you authorized using minimal scopes, please manually enter your Person URN and Member Name below to complete configuration.');
      // Clear query params to make URL clean
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setIsSaving(true);
    try {
      await saveConfig({
        linkedin_client_id: clientId,
        linkedin_client_secret: clientSecret,
        gemini_api_key: geminiKey,
        linkedin_person_urn: personUrn,
        linkedin_member_name: memberName
      });
      setMessage('Configuration updated successfully.');
      // Clear password fields, keep others
      setClientId('');
      setClientSecret('');
      setGeminiKey('');
      refreshData();
    } catch (e) {
      setError(e.message || 'Failed to save configuration.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleConnect = async () => {
    setError(null);
    setIsAuthorizing(true);
    setMessage(null);
    try {
      const res = await getAuthUrl(scopeMode);
      // Redirect browser to LinkedIn authorization portal
      window.location.href = res.auth_url;
    } catch (e) {
      setError(e.message || 'Failed to trigger OAuth flow. Make sure Client ID is configured and saved.');
      setIsAuthorizing(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your LinkedIn account?')) return;
    setError(null);
    try {
      await logout();
      setPersonUrn('');
      setMemberName('');
      refreshData();
    } catch (e) {
      setError(e.message || 'Failed to disconnect account.');
    }
  };

  const copyRedirectUri = () => {
    navigator.clipboard.writeText(redirectUri);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="overview-header">
        <h2 style={{ fontSize: '32px', marginBottom: '8px' }}>Integrations & Settings</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Configure API keys, OAuth endpoints, and developer credentials.</p>
      </div>

      {message && (
        <div style={{
          padding: '16px',
          borderRadius: '12px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          color: '#34d399',
          marginBottom: '24px',
          fontSize: '14px',
          lineHeight: '1.6'
        }}>
          {message}
        </div>
      )}

      {error && (
        <div style={{
          padding: '16px',
          borderRadius: '12px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          color: '#f87171',
          marginBottom: '24px',
          fontSize: '14px',
          lineHeight: '1.6'
        }}>
          {error}
        </div>
      )}

      <div className="grid-2">
        {/* Credentials Form */}
        <div className="glass-panel">
          <h3 style={{ fontSize: '18px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={18} style={{ color: 'var(--accent-linkedin)' }} />
            API & App Configuration
          </h3>
          <form onSubmit={handleSave}>
            <div className="form-group">
              <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>LinkedIn Client ID</span>
                {status.client_id_configured && <span style={{ color: 'var(--accent-green)', fontSize: '11px' }}>✓ Configured</span>}
              </label>
              <input 
                type="text" 
                placeholder={status.client_id_configured ? '••••••••••••••••' : 'Enter Client ID'}
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>LinkedIn Client Secret</span>
                {status.client_secret_configured && <span style={{ color: 'var(--accent-green)', fontSize: '11px' }}>✓ Configured</span>}
              </label>
              <input 
                type="password" 
                placeholder={status.client_secret_configured ? '••••••••••••••••' : 'Enter Client Secret'}
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Gemini API Key</span>
                {status.gemini_configured ? <span style={{ color: 'var(--accent-green)', fontSize: '11px' }}>✓ Configured</span> : <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Using Local Templates fallback</span>}
              </label>
              <input 
                type="password" 
                placeholder={status.gemini_configured ? '••••••••••••••••' : 'Enter Gemini API Key'}
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
              />
            </div>

            <div style={{ borderTop: '1px solid var(--glass-border)', margin: '20px 0', paddingTop: '15px' }}>
              <h4 style={{ fontSize: '14px', marginBottom: '12px', color: 'var(--text-secondary)' }}>Manual Profile Overrides</h4>
              
              <div className="form-group">
                <label>LinkedIn Person URN (format: urn:li:person:ID)</label>
                <input 
                  type="text" 
                  placeholder="e.g. urn:li:person:yrZCpj2Z12"
                  value={personUrn}
                  onChange={(e) => setPersonUrn(e.target.value.trim())}
                />
              </div>

              <div className="form-group">
                <label>Member Profile Name (for display)</label>
                <input 
                  type="text" 
                  placeholder="e.g. Raju"
                  value={memberName}
                  onChange={(e) => setMemberName(e.target.value)}
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={isSaving}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #0077b5 0%, #00a0dc 100%)',
                color: 'white',
                fontWeight: '600',
                opacity: isSaving ? 0.6 : 1
              }}
            >
              <Save size={16} />
              Save Configuration
            </button>
          </form>
        </div>

        {/* OAuth Integration Status */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Link2 size={18} style={{ color: 'var(--accent-linkedin)' }} />
            OAuth Connection
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', flex: 1 }}>
            
            {/* Required redirect URI display */}
            <div style={{
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid var(--glass-border)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>
                Authorized Redirect URI (Add to LinkedIn Developer Portal)
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <code style={{ fontFamily: 'monospace', fontSize: '13px', color: 'var(--accent-linkedin)', wordBreak: 'break-all', flex: 1 }}>
                  {redirectUri}
                </code>
                <button 
                  onClick={copyRedirectUri}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '8px',
                    borderRadius: '8px',
                    color: 'var(--text-secondary)'
                  }}
                >
                  {copied ? <ClipboardCheck size={16} style={{ color: 'var(--accent-green)' }} /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            {/* Scope Selection Box */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.01)',
              border: '1px solid var(--glass-border)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)', display: 'block', marginBottom: '10px', fontWeight: '500' }}>
                OAuth Scopes Mode (Based on App Products)
              </label>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', fontSize: '13px' }}>
                  <input 
                    type="radio" 
                    name="scopeMode" 
                    value="minimal"
                    checked={scopeMode === 'minimal'}
                    onChange={() => setScopeMode('minimal')}
                    style={{ marginTop: '3px' }}
                  />
                  <div>
                    <strong>Minimal (Recommended)</strong>
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Requests only <code>w_member_social</code> scope. Requires only <strong>"Share on LinkedIn"</strong> product. Perfect if OpenID Connect is not enabled on your developer portal app. (Manual URN entry required below).
                    </p>
                  </div>
                </label>

                <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', fontSize: '13px', borderTop: '1px solid rgba(255, 255, 255, 0.03)', paddingTop: '10px' }}>
                  <input 
                    type="radio" 
                    name="scopeMode" 
                    value="openid"
                    checked={scopeMode === 'openid'}
                    onChange={() => setScopeMode('openid')}
                    style={{ marginTop: '3px' }}
                  />
                  <div>
                    <strong>Automatic (OIDC profile retrieval)</strong>
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Requests <code>w_member_social openid profile</code>. Requires both <strong>"Share on LinkedIn"</strong> and <strong>"Sign In with LinkedIn using OIDC"</strong> products active. Auto-fetches URN and Name.
                    </p>
                  </div>
                </label>
              </div>
            </div>

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px 20px',
              background: 'rgba(255, 255, 255, 0.01)',
              border: '1px dashed var(--glass-border)',
              borderRadius: '12px',
              textAlign: 'center',
              flex: 1,
              gap: '12px'
            }}>
              {status.linkedin_connected ? (
                <>
                  <CheckCircle size={40} style={{ color: 'var(--accent-green)' }} />
                  <div>
                    <h4 style={{ fontSize: '16px', marginBottom: '2px' }}>Connected to LinkedIn</h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      Member Name: <strong>{status.linkedin_member_name || 'Manually set'}</strong>
                    </p>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px', wordBreak: 'break-all' }}>
                      URN: {status.linkedin_person_urn || 'Manually set'}
                    </p>
                  </div>
                  <button 
                    onClick={handleDisconnect}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      color: '#fca5a5',
                      fontSize: '12px'
                    }}
                  >
                    <LogOut size={12} />
                    Disconnect Account
                  </button>
                </>
              ) : (
                <>
                  <Link2 size={40} style={{ color: 'var(--text-muted)' }} />
                  <div>
                    <h4 style={{ fontSize: '16px', marginBottom: '4px' }}>Account Disconnected</h4>
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)', maxWidth: '280px', lineHeight: '1.4' }}>
                      Authorize this app with your credentials to generate publication tokens.
                    </p>
                  </div>
                  
                  <button 
                    onClick={handleConnect}
                    disabled={isAuthorizing || !status.client_id_configured}
                    style={{
                      padding: '10px 22px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #0077b5 0%, #00a0dc 100%)',
                      color: 'white',
                      fontWeight: '600',
                      fontSize: '13px',
                      opacity: (isAuthorizing || !status.client_id_configured) ? 0.6 : 1
                    }}
                  >
                    Connect LinkedIn Account
                  </button>
                  
                  {!status.client_id_configured && (
                    <span style={{ fontSize: '11px', color: 'var(--accent-amber)' }}>
                      ⚠️ Fill and save Client ID and Secret first.
                    </span>
                  )}
                </>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
