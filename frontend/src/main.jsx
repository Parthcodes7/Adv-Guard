import React, { Component, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("AdvGuard App Crash:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', maxWidth: '600px', margin: '4rem auto', background: '#131b2e', color: '#f8fafc', borderRadius: '16px', border: '1px solid rgba(239, 68, 68, 0.4)', fontFamily: 'system-ui, sans-serif', boxShadow: '0 20px 40px rgba(0,0,0,0.6)' }}>
          <h2 style={{ color: '#f87171', marginTop: 0 }}>🛡️ AdvGuard Runtime Exception</h2>
          <p style={{ color: '#cbd5e1', fontSize: '0.9rem', lineHeight: '1.5' }}>
            The interface encountered an unhandled exception:
          </p>
          <pre style={{ background: '#0a0f1d', padding: '1rem', borderRadius: '8px', overflowX: 'auto', color: '#fca5a5', fontSize: '0.85rem', border: '1px solid rgba(255,255,255,0.06)' }}>
            {this.state.error?.toString()}
          </pre>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '1.25rem', background: '#2563eb', color: 'white', border: 'none', padding: '0.65rem 1.25rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.9rem' }}
          >
            🔄 Reload Dashboard
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
