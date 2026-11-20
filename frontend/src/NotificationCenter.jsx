import { useState, useEffect, useRef, useCallback } from 'react'

// ── Audio Engine ──────────────────────────────────────────────────────────────
function playCyberChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain); gain.connect(ctx.destination)
    osc.type = 'sine'
    osc.frequency.setValueAtTime(880, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3)
    gain.gain.setValueAtTime(0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6)
    osc.start(); osc.stop(ctx.currentTime + 0.6)
  } catch (e) {
    // Web Audio not available — silent fail
  }
}

// ── Desktop Notification ──────────────────────────────────────────────────────
function showDesktopNotification(incident) {
  if (Notification.permission === 'granted') {
    new Notification(`⚠️ AdvGuard ${incident.severity} Alert`, {
      body: `Adversarial Evasion Blocked | Threat Score: ${incident.threat_score.toFixed(2)} | ε=${incident.epsilon}`,
      icon: '/favicon.ico'
    })
  }
}

// ── Toast System ──────────────────────────────────────────────────────────────
let _toastContainer = null

function getToastContainer() {
  if (!_toastContainer || !document.body.contains(_toastContainer)) {
    _toastContainer = document.createElement('div')
    _toastContainer.className = 'toast-container'
    document.body.appendChild(_toastContainer)
  }
  return _toastContainer
}

export function showToast(message, type = 'info') {
  const container = getToastContainer()
  const toast = document.createElement('div')
  toast.className = `toast ${type}`
  toast.textContent = message
  container.appendChild(toast)
  setTimeout(() => {
    toast.style.opacity = '0'
    toast.style.transform = 'translateX(50px)'
    toast.style.transition = 'opacity 0.3s, transform 0.3s'
    setTimeout(() => toast.remove(), 350)
  }, 4000)
}

// ── useIncidentPoller Hook ────────────────────────────────────────────────────
export function useIncidentPoller() {
  const [incidents, setIncidents] = useState([])
  const prevCountRef = useRef(0)

  const fetchIncidents = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/incidents')
      if (!res.ok) return
      const data = await res.json()
      const list = data.incidents || []
      setIncidents(list)

      const newCount = list.length
      if (newCount > prevCountRef.current && prevCountRef.current > 0) {
        // New incident(s) arrived
        playCyberChime()
        const newest = list[0] // sorted by threat_score desc, first is newest critical
        if (newest) showDesktopNotification(newest)
        const severity = newest?.severity || 'ALERT'
        showToast(`⚠️ New ${severity} incident detected!`, severity === 'CRITICAL' ? 'critical' : severity === 'HIGH' ? 'warning' : 'info')
      }
      prevCountRef.current = newCount
    } catch {
      // backend not ready yet — silent
    }
  }, [])

  const addLocalIncident = useCallback((result) => {
    // Optimistically create an incident from a simulation result
    const fraudRatio = (() => {
      const match = (result.cpp_report || '').match(/FRAUD NEIGHBOR RATIO[:\s]+([0-9.]+)/i)
      return match ? Math.min(1, parseFloat(match[1]) / 100) : 0
    })()
    const threatScore = 0.4 * (result.epsilon || 0) + 0.6 * fraudRatio
    const severity = threatScore > 0.7 ? 'CRITICAL' : threatScore > 0.5 ? 'HIGH' : threatScore > 0.3 ? 'WARNING' : 'SAFE'
    const incident = {
      id: `local-${Date.now()}`,
      timestamp: new Date().toISOString(),
      severity,
      threat_score: threatScore,
      epsilon: result.epsilon || 0,
      fraud_ratio: fraudRatio,
      ml_prediction: result.ml_prediction || 'Unknown',
      steps_taken: result.steps_taken || 0,
      status: 'active',
      cpp_report: result.cpp_report || ''
    }
    playCyberChime()
    showDesktopNotification(incident)
    showToast(`🛡️ Attack blocked! Threat score: ${threatScore.toFixed(2)}`, severity === 'CRITICAL' ? 'critical' : 'warning')
    setIncidents(prev => [incident, ...prev])
    prevCountRef.current = prevCountRef.current + 1
  }, [])

  useEffect(() => {
    // Request desktop notification permission
    if (Notification.permission === 'default') {
      Notification.requestPermission()
    }
    fetchIncidents()
    const id = setInterval(fetchIncidents, 3000)
    return () => clearInterval(id)
  }, [fetchIncidents])

  const unreadCount = incidents.filter(i => i.status === 'active').length

  return { incidents, unreadCount, addLocalIncident }
}

// ── AlertBell ─────────────────────────────────────────────────────────────────
export function AlertBell({ onClick, unreadCount }) {
  return (
    <button className="alert-bell-btn" onClick={onClick} title="Incident Command Center">
      🔔
      {unreadCount > 0 && (
        <span className="bell-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
      )}
    </button>
  )
}

// ── Settings Modal ────────────────────────────────────────────────────────────
function SettingsModal({ onClose }) {
  const [cfg, setCfg] = useState({
    email_enabled: false,
    smtp_host: 'smtp.gmail.com',
    smtp_port: 465,
    sender_email: '',
    sender_password: '',
    recipient_email: '',
    discord_enabled: false,
    discord_webhook_url: '',
    telegram_enabled: false,
    telegram_bot_token: '',
    telegram_chat_id: ''
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch('http://localhost:8000/api/notifications/config')
      .then(r => r.json())
      .then(data => {
        if (data) setCfg(prev => ({ ...prev, ...data }))
      })
      .catch(() => {})
  }, [])

  const toggle = (key) => setCfg(c => ({ ...c, [key]: !c[key] }))
  const set = (key, val) => setCfg(c => ({ ...c, [key]: val }))

  const testChannel = async (channel) => {
    try {
      // First save current config so backend has credentials immediately
      await fetch('http://localhost:8000/api/notifications/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg)
      })

      const res = await fetch('http://localhost:8000/api/notifications/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel })
      })
      const data = await res.json()
      if (data.success) {
        showToast(`✅ ${channel.toUpperCase()} alert sent successfully!`, 'safe')
      } else {
        showToast(`❌ ${data.error || 'Test failed'}`, 'critical')
      }
    } catch (err) {
      showToast(`❌ Could not reach backend: ${err.message}`, 'critical')
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      const res = await fetch('http://localhost:8000/api/notifications/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg)
      })
      const data = await res.json()
      showToast(data.success ? '✅ Notification config saved' : '❌ Save failed', data.success ? 'safe' : 'critical')
      if (data.success) onClose()
    } catch {
      showToast('❌ Could not reach backend', 'critical')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="settings-modal-bg" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="settings-modal" style={{ maxHeight: '90vh', overflowY: 'auto' }}>
        <h3>🔔 Notification Settings</h3>

        {/* Email */}
        <div className="settings-row">
          <span>📧 Email Alerts</span>
          <div className={`toggle-switch ${cfg.email_enabled ? 'on' : ''}`} onClick={() => toggle('email_enabled')} />
        </div>
        {cfg.email_enabled && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1rem' }}>
            <label style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Recipient Email (Where alerts will be sent):</label>
            <input className="settings-input" placeholder="e.g. your_email@gmail.com" value={cfg.recipient_email || ''}
              onChange={e => set('recipient_email', e.target.value)} />

            <label style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.3rem' }}>Sender Gmail Account:</label>
            <input className="settings-input" placeholder="e.g. sender_bot@gmail.com" value={cfg.sender_email || ''}
              onChange={e => set('sender_email', e.target.value)} />

            <label style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.3rem' }}>Sender 16-Character Google App Password:</label>
            <input className="settings-input" type="password" placeholder="16-character Google App Password" value={cfg.sender_password || ''}
              onChange={e => set('sender_password', e.target.value)} />

            <div style={{ background: 'rgba(14, 165, 233, 0.1)', border: '1px solid rgba(14, 165, 233, 0.3)', borderRadius: '6px', padding: '8px 10px', fontSize: '0.72rem', color: '#7dd3fc', lineHeight: 1.4, marginTop: '0.2rem' }}>
              ℹ️ <strong>Google Security Requirement:</strong> Gmail requires an <em>App Password</em> (not your normal password). Visit:
              <br />
              <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" style={{ color: '#38bdf8', textDecoration: 'underline' }}>
                myaccount.google.com/apppasswords
              </a>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.6rem' }}>
              <a href="http://localhost:8000/api/notifications/preview-email" target="_blank" rel="noreferrer" style={{ fontSize: '0.75rem', color: '#0ea5e9', textDecoration: 'underline' }}>
                👁️ View Rendered Email Dossier
              </a>
              <button className="action-btn" onClick={() => testChannel('email')}>Send Real Test Email</button>
            </div>
          </div>
        )}

        {/* Discord */}
        <div className="settings-row" style={{ marginTop: '1rem' }}>
          <span>🎮 Discord Webhook</span>
          <div className={`toggle-switch ${cfg.discord_enabled ? 'on' : ''}`} onClick={() => toggle('discord_enabled')} />
        </div>
        {cfg.discord_enabled && (
          <>
            <input className="settings-input" placeholder="Discord Webhook URL" value={cfg.discord_webhook_url}
              onChange={e => set('discord_webhook_url', e.target.value)} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.4rem' }}>
              <button className="action-btn" onClick={() => testChannel('discord')}>Test Discord</button>
            </div>
          </>
        )}

        {/* Telegram */}
        <div className="settings-row" style={{ marginTop: '1rem' }}>
          <span>✈️ Telegram Bot</span>
          <div className={`toggle-switch ${cfg.telegram_enabled ? 'on' : ''}`} onClick={() => toggle('telegram_enabled')} />
        </div>
        {cfg.telegram_enabled && (
          <>
            <input className="settings-input" placeholder="Telegram Bot Token" value={cfg.telegram_bot_token}
              onChange={e => set('telegram_bot_token', e.target.value)} style={{ marginBottom: '0.4rem' }} />
            <input className="settings-input" placeholder="Telegram Chat ID" value={cfg.telegram_chat_id}
              onChange={e => set('telegram_chat_id', e.target.value)} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.4rem' }}>
              <button className="action-btn" onClick={() => testChannel('telegram')}>Test Telegram</button>
            </div>
          </>
        )}

        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
          <button className="action-btn" onClick={onClose}>Cancel</button>
          <button className="action-btn" onClick={save} disabled={saving}
            style={{ background: '#0ea5e9', borderColor: '#0ea5e9', color: '#fff' }}>
            {saving ? 'Saving…' : 'Save Config'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Incident Card ─────────────────────────────────────────────────────────────
function IncidentCard({ incident, onAction, onOpenForensics }) {
  const [acting, setActing] = useState(false)
  const ts = new Date(incident.timestamp).toLocaleTimeString()
  const fraudPct = Math.round((incident.fraud_ratio || 0) * 100)

  const doAction = async (action) => {
    setActing(true)
    try {
      const res = await fetch(`http://localhost:8000/api/incidents/${incident.id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      })
      const data = await res.json()
      if (data.success) {
        onAction(incident.id, action)
        const labels = { mfa_challenge: 'MFA Challenge issued', quarantine: 'Session quarantined', immunize: 'User immunized', dismiss: 'Incident dismissed' }
        showToast(`✅ ${labels[action] || action}`, 'safe')
      }
    } catch {
      showToast('❌ Action failed — backend unreachable', 'critical')
    } finally {
      setActing(false)
    }
  }

  const statusLabel = {
    active: '🔴 Active',
    mfa_challenged: '🔵 MFA Challenged',
    quarantined: '🟠 Quarantined',
    immunized: '🟢 Immunized',
    resolved: '✅ Resolved',
    dismissed: '⚫ Dismissed'
  }[incident.status] || incident.status

  return (
    <div className={`incident-card ${incident.severity}`}>
      <span className={`severity-badge ${incident.severity}`}>{incident.severity}</span>
      <div className="incident-meta">
        <span>⚡ Score</span><span><strong>{(incident.threat_score || 0).toFixed(3)}</strong></span>
        <span>🎯 Attack</span><span>{incident.attack_method || 'FGSM'}</span>
        <span>🔍 Fraud ratio</span><span>{fraudPct}%</span>
        <span>🤖 ML</span><span>{incident.ml_prediction}</span>
        <span>🕐 Time</span><span>{ts}</span>
        <span>📋 Status</span><span>{statusLabel}</span>
      </div>

      <div style={{ margin: '0.5rem 0' }}>
        <button
          className="action-btn"
          style={{ width: '100%', borderColor: 'rgba(14, 165, 233, 0.4)', background: 'rgba(14, 165, 233, 0.1)', color: 'var(--primary)', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
          onClick={() => onOpenForensics(incident)}
        >
          📄 Autonomous AI Forensic Dossier
        </button>
      </div>

      {incident.status === 'active' && (
        <div className="incident-actions">
          <button className="action-btn" disabled={acting} onClick={() => doAction('mfa_challenge')}>📲 Issue MFA</button>
          <button className="action-btn" disabled={acting} onClick={() => doAction('quarantine')}>⛔ Quarantine</button>
          <button className="action-btn" disabled={acting} onClick={() => doAction('immunize')}>🛡️ Immunize</button>
          <button className="action-btn" disabled={acting} onClick={() => doAction('dismiss')}>✓ Dismiss</button>
        </div>
      )}
    </div>
  )
}

// ── Forensic Dossier Modal ────────────────────────────────────────────────────
function ForensicDossierModal({ incident, onClose }) {
  const [brief, setBrief] = useState(incident.forensic_brief || null)
  const [loading, setLoading] = useState(!incident.forensic_brief)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!brief) {
      fetch(`http://localhost:8000/api/incidents/${incident.id}/forensics`)
        .then(r => r.json())
        .then(data => {
          if (data?.forensics) setBrief(data.forensics)
        })
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }, [incident.id, brief])

  const copyMarkdown = () => {
    if (brief?.markdown_report) {
      navigator.clipboard.writeText(brief.markdown_report)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="settings-modal-bg" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="settings-modal forensic-modal">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-medium)', paddingBottom: '0.8rem', marginBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
              <span className="forensic-badge">INCIDENT DOSSIER</span>
              <span className={`severity-badge ${incident.severity}`}>{incident.severity}</span>
            </div>
            <h3 style={{ margin: 0, fontSize: '1.2rem' }}>AdvGuard Forensic Advisory #{incident.id}</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {brief?.timestamp || incident.timestamp} &bull; Threat Score: <strong>{(incident.threat_score || 0).toFixed(4)}</strong>
            </span>
          </div>
          <button className="action-btn" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <span className="spinner" /> Analyzing spatial manifold &amp; generating dossier…
          </div>
        ) : (
          <div className="forensic-modal-body">
            {/* Section 1: Executive Summary */}
            <div className="forensic-section">
              <h4>🛡️ Executive Incident Summary</h4>
              <p className="forensic-prose">{brief?.executive_summary}</p>
            </div>

            {/* Section 2: Attack Vector Analysis */}
            <div className="forensic-section">
              <h4>🎯 Adversarial Vector Analysis ({brief?.attack_method})</h4>
              <p className="forensic-prose">{brief?.attack_vector_analysis}</p>
              <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                <span className="distortion-pill">L₂ Euclidean: <strong>{brief?.distortion?.l2}</strong></span>
                <span className="distortion-pill">L_∞ Bound: <strong>{brief?.distortion?.linf}</strong></span>
                <span className="distortion-pill">Manipulated Features: <strong>{brief?.distortion?.changed_count}/{brief?.distortion?.total_features}</strong></span>
              </div>
            </div>

            {/* Section 3: Exploited Feature Forensics */}
            {brief?.feature_insights?.length > 0 && (
              <div className="forensic-section">
                <h4>📊 Exploited Attribute Attribution (Highest Gradient Drift)</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                  {brief.feature_insights.map((fi, i) => (
                    <div key={i} className="forensic-feature-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '0.8rem' }}>{fi.name} &bull; <small style={{ color: 'var(--text-muted)', fontWeight: 400 }}>{fi.description}</small></span>
                        <span className={`tf-delta ${fi.delta > 0 ? 'delta-pos' : 'delta-neg'}`}>
                          {fi.delta > 0 ? `+${fi.delta}` : fi.delta}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        {fi.significance} (Shift: <code>{fi.original}</code> → <code>{fi.perturbed}</code>)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Section 4: Geometric Manifold Proof */}
            <div className="forensic-section">
              <h4>🌲 Geometric Manifold &amp; Centroid Verification</h4>
              <p className="forensic-prose">{brief?.spatial_proof}</p>
            </div>

            {/* Section 5: Regulatory Compliance */}
            <div className="forensic-section">
              <h4>⚖️ Regulatory Compliance &amp; Audit Trail</h4>
              <ul className="forensic-list">
                {brief?.compliance_notes?.map((cn, i) => <li key={i}>{cn}</li>)}
              </ul>
            </div>

            {/* Section 6: Prescribed Actions */}
            <div className="forensic-section">
              <h4>⚡ Prescribed Security Countermeasures</h4>
              <ul className="forensic-list">
                {brief?.recommended_actions?.map((ra, i) => <li key={i}>{ra}</li>)}
              </ul>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-medium)', paddingTop: '1rem', marginTop: '1rem' }}>
          <button className="action-btn" onClick={copyMarkdown} disabled={!brief}>
            {copied ? '✅ Copied to Clipboard!' : '📋 Copy Full Markdown Dossier'}
          </button>
          <button className="action-btn" onClick={onClose} style={{ background: 'var(--primary)', color: '#fff', borderColor: 'var(--primary)' }}>
            Close Advisory
          </button>
        </div>
      </div>
    </div>
  )
}

// ── NotificationCenter (default export) ──────────────────────────────────────
export default function NotificationCenter({ incidents: propIncidents }) {
  const [localIncidents, setLocalIncidents] = useState(propIncidents || [])
  const [showSettings, setShowSettings] = useState(false)
  const [forensicIncident, setForensicIncident] = useState(null)

  // Sync when prop changes
  useEffect(() => {
    if (propIncidents) setLocalIncidents(propIncidents)
  }, [propIncidents])

  const handleAction = (id, action) => {
    const statusMap = {
      mfa_challenge: 'mfa_challenged',
      quarantine: 'quarantined',
      immunize: 'immunized',
      dismiss: 'dismissed'
    }
    setLocalIncidents(prev =>
      prev.map(inc => inc.id === id ? { ...inc, status: statusMap[action] || action } : inc)
    )
  }

  const sorted = [...localIncidents].sort((a, b) => (b.threat_score || 0) - (a.threat_score || 0))

  return (
    <div className="notif-center-overlay">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0 }}>⚠️ Incident Command Center</h2>
        <button className="action-btn" onClick={() => setShowSettings(true)} title="Notification Settings">⚙️ Settings</button>
      </div>

      {sorted.length === 0 ? (
        <div style={{ color: 'var(--text-muted, #888)', fontSize: '0.85rem', textAlign: 'center', marginTop: '3rem' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🛡️</div>
          No incidents detected. System clear.
        </div>
      ) : (
        sorted.map(inc => (
          <IncidentCard
            key={inc.id}
            incident={inc}
            onAction={handleAction}
            onOpenForensics={(target) => setForensicIncident(target)}
          />
        ))
      )}

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
      {forensicIncident && <ForensicDossierModal incident={forensicIncident} onClose={() => setForensicIncident(null)} />}
    </div>
  )
}
