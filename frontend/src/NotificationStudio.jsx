import React, { useState, useEffect } from 'react'

// Web Audio chime for phone alert
const playHandsetChime = (type = 'chime') => {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)

    const now = ctx.currentTime
    if (type === 'otp') {
      // Gentle double tap
      osc.type = 'sine'
      osc.frequency.setValueAtTime(587.33, now) // D5
      osc.frequency.setValueAtTime(880.00, now + 0.12) // A5
      gain.gain.setValueAtTime(0.15, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35)
      osc.start(now)
      osc.stop(now + 0.35)
    } else {
      // Tri-tone push notification
      osc.type = 'triangle'
      osc.frequency.setValueAtTime(523.25, now) // C5
      osc.frequency.setValueAtTime(659.25, now + 0.09) // E5
      osc.frequency.setValueAtTime(783.99, now + 0.18) // G5
      gain.gain.setValueAtTime(0.2, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5)
      osc.start(now)
      osc.stop(now + 0.5)
    }
  } catch (e) {
    console.warn('AudioContext not allowed or not supported yet', e)
  }
}

const TEMPLATES = [
  {
    id: 'critical_evasion',
    name: '🚨 Critical Evasion Alert',
    channel: 'push',
    priority: 'urgent',
    title: '🚨 AdvGuard CRITICAL — FGSM Evasion Blocked',
    message: 'Adversarial evasion attempt intercepted! 100% of spatial neighbors in KD-Tree are historical fraud. ML prediction overridden & funds held securely. Incident ID: #SUSPECT-8492.',
    recipient: 'advguard-alerts',
    otp: null
  },
  {
    id: 'otp_challenge',
    name: '🔐 Step-Up OTP Challenge',
    channel: 'sms',
    priority: 'high',
    title: 'AdvGuard Security: One-Time Passcode',
    message: 'AdvGuard Security: Suspicious checkout of $1,842.00 detected. Your verification code is 492-108. Valid for 5 minutes. DO NOT share this code with anyone.',
    recipient: '+1 (555) 019-2834',
    otp: '492-108'
  },
  {
    id: 'quarantine_notice',
    name: '🛡️ KD-Tree Spatial Quarantine',
    channel: 'email',
    priority: 'high',
    title: 'AdvGuard Defense Notice: Transaction Quarantined',
    message: 'A transaction mimicking legitimate features was blocked after geometric KD-Tree verification detected neighborhood anomaly (Fraud Ratio > 60%). No action required from customer.',
    recipient: 'soc-lead@cyberguard-bank.com',
    otp: null
  },
  {
    id: 'soc_status',
    name: '📢 SOC Sentinel Digest',
    channel: 'discord',
    priority: 'default',
    title: 'AdvGuard SOC Sentinel: Hourly Threat Report',
    message: 'All systems operational. LSH Cache hit rate: 94.2%. Zero zero-day evasions passed through KD-Tree defense perimeter.',
    recipient: 'https://discord.com/api/webhooks/...',
    otp: null
  }
]

export default function NotificationStudio({ incidents = [] }) {
  const [channel, setChannel] = useState('sms') // 'push', 'sms', 'email', 'discord'
  const [recipient, setRecipient] = useState('+1 (555) 019-2834')
  const [title, setTitle] = useState('AdvGuard Security: One-Time Passcode')
  const [message, setMessage] = useState('AdvGuard Security: Suspicious checkout of $1,842.00 detected. Your verification code is 492-108. Valid for 5 minutes. DO NOT share this code.')
  const [priority, setPriority] = useState('high')
  const [sending, setSending] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const [soundEnabled, setSoundEnabled] = useState(true)

  // Phone Mockup States
  const [phoneBanner, setPhoneBanner] = useState(null)
  const [smsConversation, setSmsConversation] = useState([
    {
      id: 1,
      sender: 'bank',
      text: 'AdvGuard Fraud Guard: Your card ending in 4102 was authorized for $42.50 at Blue Bottle Coffee.',
      time: '10:14 AM'
    },
    {
      id: 2,
      sender: 'bank',
      text: 'AdvGuard Security: Suspicious checkout of $1,842.00 detected. Your verification code is 492-108. Valid for 5 minutes.',
      time: 'Just now',
      otp: '492-108'
    }
  ])
  const [phoneActionStatus, setPhoneActionStatus] = useState(null) // 'verified', 'locked', null

  // Change recipient placeholder when channel changes
  const handleChannelChange = (newChan) => {
    setChannel(newChan)
    if (newChan === 'push') {
      setRecipient('advguard-alerts')
      setTitle('🚨 AdvGuard CRITICAL — Evasion Blocked')
      setPriority('urgent')
    } else if (newChan === 'sms') {
      setRecipient('+1 (555) 019-2834')
      setTitle('AdvGuard Security OTP')
      setPriority('high')
    } else if (newChan === 'email') {
      setRecipient('analyst@bank.com')
      setTitle('AdvGuard Security Incident Alert')
      setPriority('high')
    } else if (newChan === 'discord') {
      setRecipient('')
      setTitle('AdvGuard SOC Security Sentinel')
      setPriority('default')
    }
  }

  // Apply Quick-Fill Template
  const applyTemplate = (tpl) => {
    setChannel(tpl.channel)
    setRecipient(tpl.recipient)
    setTitle(tpl.title)
    setMessage(tpl.message)
    setPriority(tpl.priority)
  }

  // Send Notification
  const handleDispatch = async (e) => {
    e.preventDefault()
    setSending(true)
    setLastResult(null)

    try {
      const res = await fetch('http://localhost:8000/api/notifications/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel,
          recipient,
          title,
          message,
          priority
        })
      })
      const data = await res.json()
      setLastResult(data)

      if (soundEnabled) playHandsetChime(channel === 'sms' ? 'otp' : 'chime')

      // Update phone simulator
      const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      
      // Extract OTP if present in message
      const otpMatch = message.match(/\b\d{3}[- ]?\d{3}\b/)
      const otpCode = otpMatch ? otpMatch[0] : null

      // Push notification banner on phone
      setPhoneBanner({
        channel,
        title: title || 'AdvGuard Alert',
        message: message.slice(0, 100) + (message.length > 100 ? '...' : ''),
        time: 'Now'
      })

      // Add to SMS conversation
      setSmsConversation(prev => [
        ...prev,
        {
          id: Date.now(),
          sender: 'bank',
          text: message,
          time: nowTime,
          otp: otpCode
        }
      ])
      setPhoneActionStatus(null)

      // Auto dismiss banner after 6s
      setTimeout(() => setPhoneBanner(null), 6000)

    } catch (err) {
      setLastResult({ success: false, error: err.message })
    } finally {
      setSending(false)
    }
  }

  // Interactive buttons on phone mockup
  const handlePhoneVerify = (otp) => {
    setPhoneActionStatus('verified')
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setSmsConversation(prev => [
      ...prev,
      {
        id: Date.now(),
        sender: 'user',
        text: otp || '492108',
        time: nowTime
      },
      {
        id: Date.now() + 1,
        sender: 'bank',
        text: '✅ AdvGuard: Passcode accepted. Identity verified. Transaction approved successfully.',
        time: nowTime
      }
    ])
    if (soundEnabled) playHandsetChime('otp')
  }

  const handlePhoneDeny = () => {
    setPhoneActionStatus('locked')
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setSmsConversation(prev => [
      ...prev,
      {
        id: Date.now(),
        sender: 'user',
        text: 'STOP - I did not make this purchase',
        time: nowTime
      },
      {
        id: Date.now() + 1,
        sender: 'bank',
        text: '🛑 AdvGuard ALERT: Card has been FROZEN immediately. A security specialist has been assigned to your case #ESC-902.',
        time: nowTime
      }
    ])
    if (soundEnabled) playHandsetChime('chime')
  }

  return (
    <div className="studio-container">
      {/* Studio Header */}
      <div className="studio-header">
        <div>
          <h2>🔔 Notification Creator Studio &amp; SMS Simulator</h2>
          <p className="studio-subtitle">
            Zero-config transmission via mobile push (<code>ntfy.sh</code>), email forwarding, and interactive on-screen smartphone SMS verification.
          </p>
        </div>
        <div className="studio-controls-top">
          <button 
            type="button" 
            className={`sound-toggle-btn ${soundEnabled ? 'active' : ''}`}
            onClick={() => setSoundEnabled(v => !v)}
            title="Toggle phone sound effects"
          >
            {soundEnabled ? '🔊 Sound: ON' : '🔇 Sound: OFF'}
          </button>
          <a 
            href="https://ntfy.sh/advguard-alerts" 
            target="_blank" 
            rel="noreferrer"
            className="real-phone-link"
          >
            📱 Open Real Phone Stream (<code>ntfy.sh/advguard-alerts</code>) ↗
          </a>
        </div>
      </div>

      <div className="studio-layout">
        {/* Left Column: Notification Creator Form */}
        <div className="creator-card glass-card">
          <div className="creator-section-title">
            <span className="creator-step-badge">1</span>
            <strong>Select Channel</strong>
          </div>

          <div className="channel-tabs">
            <button
              type="button"
              className={`chan-tab ${channel === 'sms' ? 'active' : ''}`}
              onClick={() => handleChannelChange('sms')}
            >
              💬 SMS / OTP Simulator
            </button>
            <button
              type="button"
              className={`chan-tab ${channel === 'push' ? 'active' : ''}`}
              onClick={() => handleChannelChange('push')}
            >
              📱 Mobile Push (ntfy.sh)
            </button>
            <button
              type="button"
              className={`chan-tab ${channel === 'email' ? 'active' : ''}`}
              onClick={() => handleChannelChange('email')}
            >
              📧 Email Forwarder
            </button>
            <button
              type="button"
              className={`chan-tab ${channel === 'discord' ? 'active' : ''}`}
              onClick={() => handleChannelChange('discord')}
            >
              🎮 Discord Webhook
            </button>
          </div>

          <div className="creator-section-title" style={{ marginTop: '1.2rem' }}>
            <span className="creator-step-badge">2</span>
            <strong>Quick-Fill Security Templates</strong>
          </div>
          <div className="template-pills">
            {TEMPLATES.map(t => (
              <button
                key={t.id}
                type="button"
                className="template-pill"
                onClick={() => applyTemplate(t)}
              >
                {t.name}
              </button>
            ))}
          </div>

          <form onSubmit={handleDispatch} className="creator-form">
            <div className="creator-section-title" style={{ marginTop: '1.2rem' }}>
              <span className="creator-step-badge">3</span>
              <strong>Compose Security Dispatch</strong>
            </div>

            <div className="form-group">
              <label>
                {channel === 'sms' && 'Recipient Mobile Number:'}
                {channel === 'push' && 'ntfy.sh Topic Name (Subscribe on any phone or browser):'}
                {channel === 'email' && 'Recipient Email Address:'}
                {channel === 'discord' && 'Discord Webhook URL:'}
              </label>
              <input
                type="text"
                className="studio-input"
                value={recipient}
                onChange={e => setRecipient(e.target.value)}
                placeholder={
                  channel === 'sms' ? '+1 (555) 019-2834' :
                  channel === 'push' ? 'advguard-alerts' :
                  channel === 'email' ? 'analyst@bank.com' :
                  'https://discord.com/api/webhooks/...'
                }
                required
              />
              <small className="input-hint">
                {channel === 'sms' && 'Simulates transmission over banking SMS gateway with instant handset delivery.'}
                {channel === 'push' && 'Zero account needed! Open https://ntfy.sh/' + (recipient || 'advguard-alerts') + ' on phone to subscribe.'}
                {channel === 'email' && 'Relayed directly to inbox without requiring app-passwords or SMTP configuration.'}
                {channel === 'discord' && 'Broadcasts rich embeds into your Security Operations Center channel.'}
              </small>
            </div>

            <div className="form-row">
              <div className="form-group" style={{ flex: 2 }}>
                <label>Alert Title / Header:</label>
                <input
                  type="text"
                  className="studio-input"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="e.g. AdvGuard CRITICAL — FGSM Intercepted"
                  required
                />
              </div>

              <div className="form-group" style={{ flex: 1 }}>
                <label>Priority:</label>
                <select
                  className="studio-select"
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                >
                  <option value="urgent">🚨 Urgent (Max)</option>
                  <option value="high">⚠️ High</option>
                  <option value="default">ℹ️ Default</option>
                  <option value="low">💤 Low</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Notification Message Body:</label>
              <textarea
                className="studio-textarea"
                rows={4}
                value={message}
                onChange={e => setMessage(e.target.value)}
                placeholder="Enter alert text, OTP code, or forensic details..."
                required
              />
            </div>

            <button
              type="submit"
              className="studio-dispatch-btn"
              disabled={sending}
            >
              {sending ? (
                <>
                  <span className="spinner-inline" /> Disagreeing &amp; Dispatching...
                </>
              ) : (
                <>
                  🚀 Dispatch Alert ({channel.toUpperCase()})
                </>
              )}
            </button>
          </form>

          {/* Result Banner */}
          {lastResult && (
            <div className={`delivery-result ${lastResult.success ? 'success' : 'error'}`}>
              <div className="result-header">
                <strong>{lastResult.success ? '✅ Dispatch Confirmed' : '❌ Dispatch Failed'}</strong>
                <span className="badge-channel">{lastResult.channel?.toUpperCase()}</span>
              </div>
              <p className="result-details">
                {lastResult.success ? (
                  <>
                    Alert delivered successfully through AdvGuard Gateway.
                    {lastResult.stream_url && (
                      <span style={{ display: 'block', marginTop: '4px' }}>
                        🔗 Live Feed: <a href={lastResult.stream_url} target="_blank" rel="noreferrer">{lastResult.stream_url}</a>
                      </span>
                    )}
                    {lastResult.delivery?.stream_url && (
                      <span style={{ display: 'block', marginTop: '4px' }}>
                        🔗 SMS Feed: <a href={lastResult.delivery.stream_url} target="_blank" rel="noreferrer">{lastResult.delivery.stream_url}</a>
                      </span>
                    )}
                  </>
                ) : (
                  lastResult.error || 'Check backend logs for details.'
                )}
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Interactive Smartphone Mockup */}
        <div className="phone-mockup-wrapper">
          <div className="phone-chassis">
            {/* Notch / Dynamic Island */}
            <div className="phone-dynamic-island">
              <div className="island-camera" />
              <div className="island-sensor" />
            </div>

            {/* Status Bar */}
            <div className="phone-status-bar">
              <span className="phone-time">9:41</span>
              <div className="phone-icons">
                <span className="phone-sig">5G</span>
                <span className="phone-wifi">📶</span>
                <span className="phone-batt">🔋 100%</span>
              </div>
            </div>

            {/* Push Banner Popup (Animated) */}
            {phoneBanner && (
              <div className="phone-push-banner" onClick={() => setPhoneBanner(null)}>
                <div className="banner-top">
                  <span className="banner-app">🛡️ ADVGUARD SECURITY</span>
                  <span className="banner-time">{phoneBanner.time}</span>
                </div>
                <div className="banner-title">{phoneBanner.title}</div>
                <div className="banner-msg">{phoneBanner.message}</div>
              </div>
            )}

            {/* Phone Screen: Messaging App */}
            <div className="phone-app-header">
              <span className="phone-back">‹ Messages</span>
              <div className="phone-contact-info">
                <div className="phone-avatar">🛡️</div>
                <div className="phone-contact-name">
                  ADV-GUARD-SECURE <span className="verified-badge">✓</span>
                </div>
                <div className="phone-subtext">Verified Financial Sentinel</div>
              </div>
              <span className="phone-action-icon">ℹ️</span>
            </div>

            <div className="phone-messages-body">
              <div className="phone-date-divider">Today · Encrypted SMS Gateway</div>

              {smsConversation.map(msg => (
                <div
                  key={msg.id}
                  className={`sms-bubble-wrap ${msg.sender === 'user' ? 'user-wrap' : 'bank-wrap'}`}
                >
                  <div className={`sms-bubble ${msg.sender === 'user' ? 'user-bubble' : 'bank-bubble'}`}>
                    <div className="bubble-text">{msg.text}</div>
                    
                    {/* If OTP detected, show interactive quick action */}
                    {msg.otp && phoneActionStatus !== 'verified' && phoneActionStatus !== 'locked' && (
                      <div className="otp-action-panel">
                        <div className="otp-code-display">{msg.otp}</div>
                        <div className="otp-buttons">
                          <button
                            type="button"
                            className="otp-btn approve"
                            onClick={() => handlePhoneVerify(msg.otp)}
                          >
                            ✅ Verify ({msg.otp})
                          </button>
                          <button
                            type="button"
                            className="otp-btn deny"
                            onClick={handlePhoneDeny}
                          >
                            🛑 Report Fraud
                          </button>
                        </div>
                      </div>
                    )}

                    <div className="bubble-time">{msg.time}</div>
                  </div>
                </div>
              ))}

              {phoneActionStatus === 'verified' && (
                <div className="phone-status-pill approved">
                  ✅ Customer Identity Confirmed · Transaction Approved
                </div>
              )}
              {phoneActionStatus === 'locked' && (
                <div className="phone-status-pill blocked">
                  🛑 Account Locked · Escalated to Cyber Fraud Unit
                </div>
              )}
            </div>

            {/* Phone Input Bottom Bar */}
            <div className="phone-bottom-bar">
              <span className="phone-plus">+</span>
              <div className="phone-input-fake">Text Message (SMS)...</div>
              <span className="phone-mic">🎙️</span>
            </div>

            {/* Home indicator bar */}
            <div className="phone-home-bar" />
          </div>

          <div className="phone-caption">
            <strong>Interactive Handset Simulator</strong>
            <span>Receives real-time dispatches from AdvGuard notification engine with active OTP verification buttons.</span>
          </div>
        </div>
      </div>
    </div>
  )
}
