import React, { useState } from 'react';
import { Sparkles, Send, Eye, RefreshCw, AlertCircle } from 'lucide-react';
import { generateDraft, publishAdhoc } from '../utils/api';

const PRESETS = [
  'Clean Code',
  'Energy Management',
  'Technical Debt',
  'AI Augmented Engineering',
  'System Design & Scalability',
  'Developer Burnout',
  'Microservices Architecture'
];

export default function AdhocCreator({ refreshData }) {
  const [topic, setTopic] = useState(PRESETS[0]);
  const [customTopic, setCustomTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [draft, setDraft] = useState(null);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [isZoomed, setIsZoomed] = useState(false);

  const activeTopic = topic === 'Custom' ? customTopic : topic;

  const handleGenerate = async () => {
    if (topic === 'Custom' && !customTopic.trim()) {
      setError('Please specify a custom topic.');
      return;
    }
    setError(null);
    setSuccessMsg(null);
    setIsGenerating(true);
    try {
      const res = await generateDraft(activeTopic);
      setDraft(res);
    } catch (e) {
      setError(e.message || 'Generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRefreshPreview = async () => {
    if (!draft) return;
    setError(null);
    setIsGenerating(true);
    try {
      const res = await generateDraft(activeTopic, draft.commentary, draft.card_text);
      setDraft(prev => ({
        ...prev,
        card_image_base64: res.card_image_base64
      }));
    } catch (e) {
      setError(e.message || 'Failed to update image preview.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePublish = async () => {
    if (!draft) return;
    setError(null);
    setSuccessMsg(null);
    setIsPublishing(true);
    try {
      const res = await publishAdhoc(draft.commentary, draft.card_text);
      setSuccessMsg(`Post published successfully! URN: ${res.published_urn}`);
      setDraft(null);
      refreshData();
    } catch (e) {
      setError(e.message || 'Failed to publish post.');
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <div>
      <div className="overview-header">
        <h2 style={{ fontSize: '32px', marginBottom: '8px' }}>Ad-hoc Creator</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Draft, customize, and publish professional posts immediately.</p>
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

      {successMsg && (
        <div style={{
          padding: '16px',
          borderRadius: '12px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          color: '#34d399',
          marginBottom: '24px',
          fontSize: '14px'
        }}>
          ✨ {successMsg}
        </div>
      )}

      <div className="glass-panel" style={{ marginBottom: '30px' }}>
        <h3 style={{ fontSize: '18px', marginBottom: '16px' }}>Configure Topic</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', alignItems: 'flex-end' }}>
          
          <div className="form-group" style={{ margin: 0, flex: 1, minWidth: '220px' }}>
            <label>Choose a Presets Topic</label>
            <select value={topic} onChange={(e) => setTopic(e.target.value)} style={{ width: '100%' }}>
              {PRESETS.map((t, idx) => (
                <option key={idx} value={t}>{t}</option>
              ))}
              <option value="Custom">-- Custom Topic --</option>
            </select>
          </div>

          {topic === 'Custom' && (
            <div className="form-group" style={{ margin: 0, flex: 1, minWidth: '220px' }}>
              <label>Enter Custom Topic</label>
              <input 
                type="text" 
                placeholder="e.g. Docker Optimization Tips"
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          )}

          <button 
            onClick={handleGenerate}
            disabled={isGenerating}
            style={{
              padding: '12px 24px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #0077b5 0%, #00a0dc 100%)',
              color: 'white',
              fontWeight: '600',
              opacity: isGenerating ? 0.6 : 1,
              height: '45px'
            }}
          >
            {isGenerating ? <RefreshCw className="animate-spin" size={18} /> : <Sparkles size={18} />}
            {draft ? 'Regenerate Draft' : 'Generate AI Draft'}
          </button>
        </div>
      </div>

      {draft && (
        <div className="grid-2">
          {/* Post Content Customizer */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>Customize Post Details</h3>
            
            <div className="form-group" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <label>LinkedIn Commentary Text</label>
              <textarea 
                value={draft.commentary}
                onChange={(e) => setDraft({ ...draft, commentary: e.target.value })}
                style={{ width: '100%', flex: 1, minHeight: '180px', resize: 'vertical', lineHeight: '1.5' }}
              />
            </div>

            <div className="form-group">
              <label>Graphic Card Text (Under 50 chars)</label>
              <input 
                type="text" 
                maxLength={50}
                value={draft.card_text}
                onChange={(e) => setDraft({ ...draft, card_text: e.target.value })}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
              <button 
                onClick={handleRefreshPreview}
                disabled={isGenerating}
                style={{
                  padding: '10px 18px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--glass-border)',
                  color: 'var(--text-primary)',
                  fontSize: '13px'
                }}
              >
                <Eye size={16} />
                Update Preview Card
              </button>

              <button 
                onClick={handlePublish}
                disabled={isPublishing}
                style={{
                  padding: '10px 20px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: 'white',
                  fontWeight: '600',
                  marginLeft: 'auto',
                  opacity: isPublishing ? 0.6 : 1
                }}
              >
                {isPublishing ? <RefreshCw className="animate-spin" size={16} /> : <Send size={16} />}
                Publish Live to LinkedIn
              </button>
            </div>
          </div>

          {/* Visual Graphic Preview */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>Visual Graphic Preview</h3>
            
            <div 
              className="card-preview-box"
              onClick={() => draft.card_image_base64 && setIsZoomed(true)}
              style={{ cursor: draft.card_image_base64 ? 'zoom-in' : 'default', position: 'relative' }}
            >
              {draft.card_image_base64 ? (
                <>
                  <img 
                    src={draft.card_image_base64} 
                    alt="LinkedIn Card Preview" 
                    className="card-preview-img" 
                  />
                  <div style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    background: 'rgba(0,0,0,0.6)',
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    pointerEvents: 'none'
                  }}>
                    🔍 Click to zoom
                  </div>
                </>
              ) : (
                <div style={{ color: 'var(--text-secondary)' }}>Rendering image...</div>
              )}
            </div>
            
            <div style={{
              padding: '14px',
              borderRadius: '10px',
              background: 'rgba(0, 119, 181, 0.05)',
              border: '1px solid rgba(0, 119, 181, 0.1)',
              fontSize: '12px',
              color: 'var(--text-secondary)',
              lineHeight: '1.6'
            }}>
              💡 <strong>Card Rendering Engine:</strong> Real-time Pillow-rendered typography cards. When you click <em>Update Preview Card</em>, the backend redraws the typography using macOS system fonts and updates the preview instantly.
            </div>
          </div>
        </div>
      )}
      {/* Zoom Modal Overlay */}
      {isZoomed && draft && draft.card_image_base64 && (
        <div 
          onClick={() => setIsZoomed(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
            cursor: 'zoom-out'
          }}
        >
          <img 
            src={draft.card_image_base64} 
            alt="LinkedIn Card Preview Full" 
            style={{
              maxHeight: '92vh',
              maxWidth: '92vw',
              borderRadius: '8px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
              border: '1px solid rgba(255,255,255,0.1)'
            }}
          />
        </div>
      )}
    </div>
  );
}
