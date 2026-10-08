import { useState, useRef } from 'react'
import './index.css'

// ── Concept Glossary data ─────────────────────────────────────────────────────
const CONCEPTS = [
  {
    icon: '🌲',
    term: 'KD-Tree (K-Dimensional Tree)',
    complexity: 'O(log N) search',
    color: 'cyan',
    desc: 'A binary space-partitioning tree that splits high-dimensional data by alternating axes at each level. Think of it like a recursive binary search, but in N dimensions. AdvGuard uses it to find the 10 closest historical transactions in O(log N) time — far faster than scanning all records linearly.'
  },
  {
    icon: '#️⃣',
    term: 'LSH (Locality-Sensitive Hashing)',
    complexity: 'O(1) fast-path',
    color: 'purple',
    desc: 'A hashing technique that maps similar high-dimensional vectors to the same "bucket" with high probability. AdvGuard uses random projection hyperplanes (Gaussian vectors) to hash transactions. If an incoming transaction lands in the same bucket as a known attack template, it is flagged instantly — before even touching the KD-Tree.'
  },
  {
    icon: '🎯',
    term: 'Adversarial Evasion Attack',
    complexity: 'White-box attack',
    color: 'red',
    desc: 'A hacker takes a known fraudulent transaction and applies tiny feature perturbations (controlled by ε) in each iteration, nudging the feature vector toward the ML model\'s "safe" decision boundary. The ML model is fooled because it evaluates features locally; it cannot see that the transaction is spatially surrounded by historical fraud.'
  },
  {
    icon: '⚖️',
    term: 'Fraud Neighbor Ratio (Override Logic)',
    complexity: '60% threshold',
    color: 'green',
    desc: 'After the KD-Tree search, AdvGuard counts what fraction of the k nearest neighbors are labeled FRAUD. If this ratio exceeds 60%, the transaction is sitting inside a fraud cluster — regardless of what the ML model says. AdvGuard then overrides the ML model and blocks the transaction.'
  },
]

// ── helpers ──────────────────────────────────────────────────────────────────
const parseCppReport = (raw) => {
  if (!raw) return {}
  const out = { neighbors: [], fraudRatio: null, verdict: null, lshHit: false }

  raw.split('\n').forEach(line => {
    // Match C++ output format: "  Neighbor 1 (ID: HIST_123) | Distance: 1.234 | Label: Safe"
    const nbMatch = line.match(/Neighbor\s+(\d+).*\|\s*Distance:\s*([0-9.]+)\s*\|\s*Label:\s*(\w+)/i)
    if (nbMatch) {
      out.neighbors.push({ id: +nbMatch[1], dist: +parseFloat(nbMatch[2]).toFixed(4), label: nbMatch[3].toUpperCase() })
    }
    // C++ outputs as a percentage (e.g. "10.0%"), so divide by 100 to store as fraction (0-1)
    const ratioMatch = line.match(/FRAUD NEIGHBOR RATIO[:\s]+([0-9.]+)/i)
    if (ratioMatch) {
      let r = parseFloat(ratioMatch[1]);
      out.fraudRatio = Math.min(1.0, Math.max(0.0, r / 100));
    }
    if (/BLOCKED/i.test(line)) out.verdict = 'BLOCKED'
    if (/APPROVED/i.test(line)) out.verdict = 'APPROVED'
    if (/LSH.*HIT|HIT.*LSH/i.test(line)) out.lshHit = true
  })
  return out
}

const EPSILON_PRESETS = [
  { label: 'Subtle ε=0.05', value: 0.05 },
  { label: 'Moderate ε=0.1', value: 0.1 },
  { label: 'Aggressive ε=0.3', value: 0.3 },
]

// ── sub-components ────────────────────────────────────────────────────────────

// Collapsible DSA glossary
const ConceptGlossary = () => {
  const [open, setOpen] = useState(false)
  return (
    <div className="glossary-wrap">
      <button className="glossary-toggle" onClick={() => setOpen(o => !o)}>
        <span>📚 DSA Concepts Used in This Project</span>
        <span className={`chevron ${open ? 'chevron-open' : ''}`}>▾</span>
      </button>
      {open && (
        <div className="glossary-grid">
          {CONCEPTS.map(c => (
            <div key={c.term} className={`concept-card concept-${c.color}`}>
              <div className="concept-header">
                <span className="concept-icon">{c.icon}</span>
                <div>
                  <div className="concept-term">{c.term}</div>
                  <div className={`concept-complexity concept-${c.color}`}>{c.complexity}</div>
                </div>
              </div>
              <p className="concept-desc">{c.desc}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Reusable insight callout box
const InsightBox = ({ color = 'cyan', icon = 'ℹ️', title, children }) => (
  <div className={`insight-box insight-${color}`}>
    <div className="insight-header">
      <span className="insight-icon">{icon}</span>
      <span className="insight-title">{title}</span>
    </div>
    <div className="insight-body">{children}</div>
  </div>
)

// Plain-English narrative shown below results
const NarrativeSummary = ({ result, parsed, blocked, steps, epsilon }) => {
  const changedCount = result.perturbed_features.filter((v, i) => Math.abs(v - result.original_features[i]) > 0.0001).length
  const fraudPct = parsed?.fraudRatio != null ? Math.round(parsed.fraudRatio * 100) : null
  return (
    <div className="glass-card narrative-card">
      <h3>📖 What Just Happened? — Plain-English Summary</h3>
      <div className="narrative-body">
        <div className="narrative-step">
          <div className="nstep-num">①</div>
          <div className="nstep-text">
            <strong>The attacker started with a known fraudulent transaction</strong> from the historical dataset
            (a real fraud record that the Random Forest correctly identified as fraud).
          </div>
        </div>
        <div className="narrative-step">
          <div className="nstep-num">②</div>
          <div className="nstep-text">
            <strong>The evasion attack ran for {steps} iterations</strong>, nudging {changedCount} of the
            {' '}{result.perturbed_features.length} transaction features by up to ε={epsilon} per step.
            Each change is tiny — comparable to rounding a dollar amount to a slightly different cent.
            Yet the cumulative effect moves the transaction's feature vector just across the Random Forest's decision boundary.
          </div>
        </div>
        <div className="narrative-step">
          <div className="nstep-num">③</div>
          <div className="nstep-text">
            <strong>The Random Forest was fooled</strong> — it now predicts the transaction is <em>Safe (Class 0)</em>.
            This is a real vulnerability in production fraud detection systems: an attacker with knowledge of
            the model (white-box attack) can reliably craft evasion samples like this.
          </div>
        </div>
        <div className="narrative-step">
          <div className="nstep-num">④</div>
          <div className="nstep-text">
            <strong>AdvGuard's C++ engine performed a geometric check</strong> using a custom KD-Tree
            (binary space-partitioning tree, O(log N) search). It found the nearest historical transactions
            in the same feature space and computed their fraud ratio.
            {fraudPct != null && <> The neighborhood was <strong>{fraudPct}% fraudulent</strong>.</>}
          </div>
        </div>
        <div className="narrative-step">
          <div className={`nstep-num ${blocked ? 'nstep-blocked' : 'nstep-allowed'}`}>⑤</div>
          <div className="nstep-text">
            {blocked
              ? <><strong>AdvGuard overrode the ML model and BLOCKED the transaction.</strong> Because
                  {fraudPct != null ? ` ${fraudPct}%` : ' the majority'} of the closest neighbors were
                  historical fraud, the geometric evidence was strong enough to reject the ML model's
                  "safe" verdict. The attacker's perturbations changed the feature values, but could not
                  escape the fraud cluster in high-dimensional space.
                </>
              : <><strong>The transaction passed through AdvGuard's check.</strong> The geometric
                  neighborhood was not fraudulent enough (below 60% threshold) to override the ML model.
                  This can happen with a very large ε — the attacker may have moved the transaction
                  far enough away from known fraud clusters. Try a smaller ε to see AdvGuard block it.
                </>
            }
          </div>
        </div>
      </div>
      {blocked && (
        <div className="narrative-conclusion conclusion-success">
          🏆 <strong>Core DSA insight demonstrated:</strong> Custom geometric data structures (KD-Tree + LSH)
          can catch adversarial ML attacks that evade statistical models — purely through spatial reasoning,
          with no ML of their own.
        </div>
      )}
      {!blocked && (
        <div className="narrative-conclusion conclusion-warn">
          💡 <strong>Try reducing ε</strong> (e.g. 0.05) — a subtler attack keeps the transaction closer
          to the fraud cluster, making it easier for AdvGuard to detect geometrically.
        </div>
      )}
    </div>
  )
}

const PipelineStep = ({ num, title, status, children }) => {
  const cls = { active: 'pipe-active', success: 'pipe-success', danger: 'pipe-danger', warn: 'pipe-warn', idle: 'pipe-idle' }[status] || 'pipe-idle'
  return (
    <div className={`pipeline-step ${cls}`}>
      <div className="pipe-num">{num}</div>
      <div className="pipe-body">
        <div className="pipe-title">{title}</div>
        {children}
      </div>
    </div>
  )
}

const NeighborBar = ({ n }) => {
  const isFraud = n.label === 'FRAUD'
  return (
    <div className="neighbor-row">
      <span className="neighbor-id">#{n.id}</span>
      <div className="neighbor-bar-wrap">
        <div className={`neighbor-bar-fill ${isFraud ? 'bar-fraud' : 'bar-safe'}`} style={{ width: `${Math.min(100, n.dist * 30)}%` }} />
      </div>
      <span className="neighbor-dist">{n.dist}</span>
      <span className={`neighbor-label ${isFraud ? 'lbl-fraud' : 'lbl-safe'}`}>{n.label}</span>
    </div>
  )
}

const FraudGauge = ({ ratio }) => {
  // ratio is already stored as a fraction (0-1), multiply by 100 for display
  const pct = Math.min(100, Math.round((ratio ?? 0) * 100))
  const color = pct > 60 ? 'var(--accent-red)' : pct > 40 ? 'var(--accent-amber)' : 'var(--accent-green)'
  const circ = 2 * Math.PI * 44
  const dash = circ - (pct / 100) * circ
  return (
    <div className="gauge-wrap">
      <svg width="120" height="120" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="44" fill="none" stroke="var(--border-light)" strokeWidth="10" />
        <circle cx="50" cy="50" r="44" fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circ} strokeDashoffset={dash} strokeLinecap="round"
          style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%', transition: 'stroke-dashoffset 1s ease' }} />
        <text x="50" y="54" textAnchor="middle" fill={color} fontSize="18" fontWeight="800" fontFamily="JetBrains Mono">{pct}%</text>
      </svg>
      <div className="gauge-label">Fraud Ratio<br/>in Neighborhood</div>
    </div>
  )
}

// ── main app ──────────────────────────────────────────────────────────────────
function App() {
  const [epsilon, setEpsilon] = useState(0.1)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [parsed, setParsed] = useState(null)
  const [error, setError] = useState(null)
  const [phase, setPhase] = useState(0)
  const resultsRef = useRef(null)

  const simulateAttack = async () => {
    setLoading(true); setError(null); setResult(null); setParsed(null); setPhase(1)
    try {
      await new Promise(r => setTimeout(r, 500))
      setPhase(2)
      const response = await fetch('http://localhost:8000/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ epsilon })
      })
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to execute attack')
      }
      const data = await response.json()
      setResult(data)
      setParsed(parseCppReport(data.cpp_report))
      setPhase(3)
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300)
    } catch (err) {
      setError(err.message); setPhase(0)
    } finally {
      setLoading(false)
    }
  }

  const blocked = result?.advguard_blocked
  const steps = result?.steps_taken ?? 0

  return (
    <>
      {/* Header */}
      <header className="app-header">
        <div className="header-logo">
          <div className="logo-shield">🛡️</div>
          <div>
            <h1>AdvGuard</h1>
            <div className="header-tagline">Geometric Evasion Defense · Financial ML Security</div>
          </div>
        </div>
        <div className="header-badges">
          <span className="hbadge cyan">KD-Tree O(log N)</span>
          <span className="hbadge red">Adversarial ML</span>
          <span className="hbadge green">LSH O(1)</span>
        </div>
      </header>

      {/* Verdict Banner */}
      {result && (
        <div className={`verdict-banner ${blocked ? 'banner-blocked' : 'banner-allowed'}`}>
          <div className="verdict-icon">{blocked ? '🛡️' : '🚨'}</div>
          <div className="verdict-text">
            <strong>{blocked ? 'ATTACK BLOCKED BY ADVGUARD' : 'ATTACK SUCCESSFUL (FRAUD ESCAPED)'}</strong>
            <span>{blocked
              ? `The ML model was tricked, but AdvGuard's geometric engine caught the anomaly and blocked the fraud.`
              : `The ML model was tricked into approving the fraud, and AdvGuard did not detect enough nearby historical fraud to override it.`}</span>
          </div>
          <div className="verdict-steps">
            <div className="vstep-num">{steps}</div>
            <div className="vstep-lbl">perturbation<br/>steps</div>
          </div>
        </div>
      )}

      {/* DSA Concepts Glossary */}
      <ConceptGlossary />

      {/* Pipeline Diagram */}
      <section className="pipeline-section">
        <h2 className="section-title">Attack &amp; Defense Pipeline</h2>
        <div className="pipeline-track">
          <PipelineStep num="1" title="Attacker's Goal" status={phase >= 1 ? 'success' : 'idle'}>
            <p>Take a known <strong>Fraudulent</strong> transaction and modify it slightly to bypass detection.</p>
          </PipelineStep>
          <div className="pipe-arrow">→</div>
          <PipelineStep num="2" title={`Evasion Attack (ε=${epsilon})`} status={phase === 1 ? 'active' : phase >= 2 ? 'danger' : 'idle'}>
            <p>Features are nudged by <strong>ε={epsilon}</strong> per step until the ML model makes a mistake.</p>
            {phase >= 2 && result && <div className="pipe-stat">{steps} steps taken</div>}
          </PipelineStep>
          <div className="pipe-arrow">→</div>
          <PipelineStep num="3" title="ML Model — Tricked!" status={phase >= 2 ? 'danger' : 'idle'}>
            <p>The ML model is fooled and incorrectly classifies the modified fraud as <strong>Legitimate / Safe</strong>.</p>
            {phase >= 3 && <div className="pipe-stat ml-fooled">❌ ML Prediction: Legitimate</div>}
          </PipelineStep>
          <div className="pipe-arrow">→</div>
          <PipelineStep num="4" title="AdvGuard C++ Engine" status={phase === 2 ? 'active' : phase === 3 ? (blocked ? 'success' : 'warn') : 'idle'}>
            <p>Checks the transaction's true coordinates against historical fraud using KD-Trees.</p>
            {phase >= 3 && (
              <div className={`pipe-stat ${blocked ? 'stat-green' : 'stat-amber'}`}>
                {blocked ? '🛡️ BLOCKED (Fraud Detected)' : '⚠️ ALLOWED (Fraud Escaped)'}
              </div>
            )}
          </PipelineStep>
        </div>
      </section>

      {/* Controls */}
      <section className="controls-section glass-card">
        <h2>Configure &amp; Launch Attack</h2>
        <div className="controls-grid">
          <div className="control-group">
            <label className="ctrl-label">
              Perturbation Strength &nbsp;<span className="epsilon-val">ε = {epsilon}</span>
            </label>
            <input type="range" min="0.01" max="0.5" step="0.01" value={epsilon}
              onChange={e => setEpsilon(+e.target.value)} className="epsilon-slider" disabled={loading} />
            <div className="preset-row">
              {EPSILON_PRESETS.map(p => (
                <button key={p.value} className={`preset-btn ${epsilon === p.value ? 'preset-active' : ''}`}
                  onClick={() => setEpsilon(p.value)} disabled={loading}>{p.label}</button>
              ))}
            </div>
          </div>
          <div className="launch-group">
            <button className="btn btn-danger launch-btn" onClick={simulateAttack} disabled={loading}>
              {loading ? <><span className="spinner" /> Running Simulation…</> : '⚡ Launch Evasion Attack'}
            </button>
            {error && <div className="error-msg">⛔ {error}</div>}
          </div>
        </div>
      </section>

      {/* Results */}
      {result && (
        <div ref={resultsRef} className="results-grid">

          {/* Feature Perturbation Map */}
          <div className="glass-card result-card">
            <h3>Feature Perturbation Map</h3>
            <p className="card-desc">Each box is one numerical feature of the transaction (e.g. amount, velocity). Red pulsing boxes were altered by the attacker.</p>

            <InsightBox color="red" icon="⚠️" title="Why this is dangerous">
              The attacker changed {result.perturbed_features.filter((v, i) => Math.abs(v - result.original_features[i]) > 0.0001).length} out
              of {result.perturbed_features.length} features by at most ε={epsilon} per step, over {steps} iterations.
              Each individual change is so small it looks like normal rounding noise — yet together they completely
              flip the ML model's prediction from <strong>FRAUD → SAFE</strong>.
              This is why ML models alone are insufficient for high-stakes financial decisions.
            </InsightBox>

            <div className="feature-legend" style={{marginTop:'1rem'}}>
              <span className="leg-dot leg-changed" /> Changed (Δ shown below) &nbsp;&nbsp;
              <span className="leg-dot leg-orig" /> Unchanged
            </div>
            <div className="feature-grid">
              {result.perturbed_features.map((val, idx) => {
                const orig = result.original_features[idx]
                const changed = Math.abs(val - orig) > 0.0001
                const delta = (val - orig).toFixed(3)
                return (
                  <div key={idx} className={`feature-box ${changed ? 'changed' : ''}`} title={changed ? `Original: ${orig.toFixed(3)} → Perturbed: ${val.toFixed(3)} (Δ=${delta})` : `F${idx+1} = ${val.toFixed(3)} (unchanged)`}>
                    <div className="feat-label">F{idx + 1}</div>
                    <div className="feat-val">{val.toFixed(2)}</div>
                    {changed && <div className="feat-delta">{+delta > 0 ? '+' : ''}{delta}</div>}
                  </div>
                )
              })}
            </div>
            <p className="card-footnote">💡 Hover any box to see the exact original → perturbed values and Δ change.</p>
          </div>

          {/* KD-Tree Neighbors */}
          <div className="glass-card result-card">
            <h3>KD-Tree Nearest Neighbors</h3>
            <p className="card-desc">
              The C++ KD-Tree searched the entire historical transaction database and returned the {parsed?.neighbors.length || 10} spatially
              closest records. Bar length = Euclidean distance (shorter bar = closer neighbor).
            </p>

            <div className="neighbors-gauge-row">
              <div className="neighbors-list">
                {parsed?.neighbors.length > 0
                  ? parsed.neighbors.map(n => <NeighborBar key={n.id} n={n} />)
                  : <div className="no-neighbors">See raw output below — neighbor lines not detected in this engine build.</div>}
              </div>
              <FraudGauge ratio={parsed?.fraudRatio} />
            </div>

            {parsed?.fraudRatio != null && (
              <div className={`fraud-ratio-badge ${parsed.fraudRatio > 0.6 ? 'badge-red' : 'badge-amber'}`}>
                {Math.round(parsed.fraudRatio * 100)}% of nearest neighbors are FRAUD —
                {parsed.fraudRatio > 0.6 ? ' override threshold exceeded ✓' : ' below override threshold'}
              </div>
            )}

            <InsightBox
              color={parsed?.fraudRatio > 0.6 ? 'green' : 'amber'}
              icon={parsed?.fraudRatio > 0.6 ? '🌐' : '🔍'}
              title={parsed?.fraudRatio > 0.6 ? 'Why AdvGuard blocked it' : 'Why AdvGuard allowed it'}
            >
              {parsed?.fraudRatio > 0.6
                ? <>The perturbed transaction now sits at coordinates where
                  {' '}<strong>{Math.round((parsed?.fraudRatio ?? 0) * 100)}%</strong> of its closest
                  historical neighbors were real fraud cases.
                  The ML model was fooled by the surface-level feature values, but <strong>the transaction's
                  position in feature space has not changed enough</strong> — it is still geometrically inside
                  a fraud cluster. AdvGuard's KD-Tree reveals this and overrides the ML verdict.
                  </>
                : <>The perturbed transaction landed in a region where fewer than 60% of
                  its nearest neighbors are fraud. AdvGuard requires a supermajority (60%+)
                  before overriding the ML model to avoid false positives on legitimate transactions
                  that happen to be close to fraud clusters.
                  </>
              }
            </InsightBox>
          </div>

          {/* Raw C++ Output + Engine Summary */}
          <div className="glass-card result-card full-width-card">
            <h3>C++ Engine Raw Console Output</h3>
            <p className="card-desc">
              This is the live stdout from the compiled C++ binary (<code>advguard_engine.exe</code>).
              Color coding: <span className="inline-tag purple">purple</span> = LSH check,
              <span className="inline-tag cyan"> cyan</span> = fraud ratio computation,
              <span className="inline-tag green"> green</span> = final block/approve verdict.
            </p>
            <div className="console-split">
              <div className="terminal-container">
                <div className="terminal-header">
                  <div className="terminal-dots">
                    <span className="tdot tdot-red" />
                    <span className="tdot tdot-yellow" />
                    <span className="tdot tdot-green" />
                  </div>
                  <span className="terminal-title">advguard_engine.exe — stdout</span>
                </div>
                <div className="console-output">
                  {result.cpp_report.split('\n').map((line, i) => {
                    let cls = ''
                    if (/BLOCKED/i.test(line)) cls = 'highlight-green'
                    if (/APPROVED/i.test(line)) cls = 'highlight-amber'
                    if (/FRAUD NEIGHBOR RATIO/i.test(line)) cls = 'highlight-cyan'
                    if (/LSH/i.test(line)) cls = 'highlight-purple'
                    if (/distance=/i.test(line)) cls = 'highlight-dim'
                    return <div key={i} className={cls}>{line || '\u00A0'}</div>
                  })}
                </div>
              </div>
              <div className="engine-summary">
                <h4>Decision Logic</h4>
                <div className="decision-steps">
                  <div className={`decision-step ${parsed?.lshHit ? 'ds-triggered' : 'ds-passed'}`}>
                    <span className="ds-num">1</span>
                    <div>
                      <div className="ds-label">LSH Fast-Path Check</div>
                      <div className="ds-detail">
                        {parsed?.lshHit
                          ? 'Known attack template detected via hash bucket. Blocked immediately without KD-Tree search.'
                          : 'No matching hash bucket. Transaction is not a known template attack. Proceed to KD-Tree.'}
                      </div>
                    </div>
                  </div>
                  <div className="decision-step ds-passed">
                    <span className="ds-num">2</span>
                    <div>
                      <div className="ds-label">KD-Tree Spatial Search</div>
                      <div className="ds-detail">
                        Found {parsed?.neighbors.length ?? '?'} nearest neighbors in O(log N) time by
                        recursively partitioning the feature space and using a Max-Heap to track the closest k points.
                      </div>
                    </div>
                  </div>
                  <div className="decision-step ds-passed">
                    <span className="ds-num">3</span>
                    <div>
                      <div className="ds-label">Fraud Ratio Calculation</div>
                      <div className="ds-detail">
                        {parsed?.fraudRatio != null
                          ? <>{Math.round(parsed.fraudRatio * 100)}% of the {parsed?.neighbors.length ?? '?'} neighbors
                            are labeled FRAUD. Threshold is <strong>&gt;60%</strong>.
                            {parsed.fraudRatio > 0.6 ? ' Threshold exceeded.' : ' Threshold not reached.'}
                            </>
                          : 'Ratio parsed from raw output.'}
                      </div>
                    </div>
                  </div>
                  <div className={`decision-step ${blocked ? 'ds-blocked' : 'ds-allowed'}`}>
                    <span className="ds-num">4</span>
                    <div>
                      <div className="ds-label">Override Decision</div>
                      <div className="ds-detail">
                        {blocked
                          ? 'Fraud ratio exceeded threshold. AdvGuard overrides Random Forest prediction and BLOCKS the transaction.'
                          : 'Fraud ratio below threshold. AdvGuard defers to the Random Forest. Transaction passes through.'}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="esummary-row" style={{marginTop:'1rem', paddingTop:'0.75rem', borderTop:'1px solid var(--border-light)'}}>
                  <span>ε used</span><span className="tag-purple">{epsilon}</span>
                </div>
                <div className="esummary-row"><span>Perturbation steps</span><span className="tag-purple">{steps}</span></div>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* What just happened? narrative */}
      {result && <NarrativeSummary result={result} parsed={parsed} blocked={blocked} steps={steps} epsilon={epsilon} />}

      {/* Idle placeholder */}
      {!result && !loading && (
        <div className="idle-placeholder">
          <div className="idle-icon">🛡️</div>
          <div className="idle-title">Ready to simulate</div>
          <div className="idle-sub">Configure ε above and launch the attack to see the full pipeline in action.</div>
          <div className="idle-hint">Try different ε values to see how attack strength affects whether AdvGuard catches it.</div>
        </div>
      )}

      <footer className="app-footer">
        AdvGuard · Data Structures &amp; Algorithms Course Project · KD-Tree + LSH + Adversarial ML
      </footer>
    </>
  )
}

export default App
