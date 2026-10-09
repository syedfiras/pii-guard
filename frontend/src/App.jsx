import { useState } from 'react'
import './App.css'

const API = 'http://127.0.0.1:8000'

const PRESETS = {
  all: {
    label: 'All combined (demo)',
    text: 'Hi, I am Ravi Kumar. My email is ravi.k@test.com, call me on 9876543210. PAN ABCDE1234F, Aadhaar 2344 5678 9012.',
  },
  email: { label: 'Email only', text: 'Please send invoice to priya.sharma@test.com urgently.' },
  phone: { label: 'Phone only', text: 'Call me back on +91-98765 43210 tomorrow morning.' },
  pan: { label: 'PAN only', text: 'My PAN for KYC is BNZPM5678K, please verify.' },
  aadhaar: { label: 'Aadhaar only', text: 'Aadhaar number 2344 5678 9012 for address proof.' },
}

const TYPE_HELP = {
  EMAIL: 'like name@test.com',
  PHONE: '10-digit Indian mobile',
  PAN: 'ABCDE1234F format',
  AADHAAR: '12-digit number',
}

function highlight(text, detections, cls) {
  if (!detections?.length || !text) return text
  // sort longest values first to avoid partial overlap
  const vals = [...new Set(detections.map((d) => d.value))].sort((a, b) => b.length - a.length)
  // split by values
  let parts = [text]
  vals.forEach((v) => {
    const next = []
    parts.forEach((p) => {
      if (typeof p !== 'string') { next.push(p); return }
      const split = p.split(v)
      split.forEach((s, i) => {
        next.push(s)
        if (i < split.length - 1) next.push({ __mark: v })
      })
    })
    parts = next
  })
  return parts.map((p, i) =>
    typeof p === 'string' ? <span key={i}>{p}</span> :
      <mark key={i} className={cls} title="Detected PII">{p.__mark}</mark>
  )
}

function toText(payload) {
  if (typeof payload === 'string') return payload
  if (payload && typeof payload === 'object' && typeof payload.text === 'string' && Object.keys(payload).length === 1) return payload.text
  return JSON.stringify(payload, null, 2)
}

export default function App() {
  const [input, setInput] = useState(PRESETS.all.text)
  const [types, setTypes] = useState(['EMAIL', 'PHONE', 'PAN', 'AADHAAR'])
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [step, setStep] = useState(0) // 0 idle, 1 typed, 2 scanned, 3 sent, 4 restored
  const [tests, setTests] = useState(null)
  const [testing, setTesting] = useState(false)

  const toggle = (t) => setTypes((p) => p.includes(t) ? p.filter((x) => x !== t) : [...p, t])

  const send = async (textOverride) => {
    const text = textOverride ?? input
    if (!text.trim()) { setErr('Type a message first.'); return }
    setLoading(true); setErr(''); setStep(1)
    try {
      const r = await fetch(`${API}/api/invoke`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: 'send_sms', payload: { text }, types }),
      })
      setStep(2)
      if (!r.ok) throw new Error('Backend not running. Start: python -m uvicorn app:app --port 8000 (in backend/)')
      const data = await r.json()
      setStep(3)
      await new Promise((x) => setTimeout(x, 250))
      setRes({ ...data, original: text })
      setStep(4)
    } catch (e) { setErr(e.message); setStep(0) }
    finally { setLoading(false) }
  }

  const runTests = async () => {
    setTesting(true); setTests(null)
    const cases = Object.entries(PRESETS).map(([k, v]) => ({ name: k, text: v.text }))
    const rows = []
    for (const c of cases) {
      try {
        const r = await fetch(`${API}/api/invoke`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tool: 'send_sms', payload: { text: c.text }, types }),
        })
        const d = await r.json()
        const leaked = (d.detections || []).some((x) => JSON.stringify(d.tool_saw).includes(x.value))
        rows.push({ name: c.name, found: d.detections?.length ?? 0, leak: d.leak_check, leaked, ms: d.latency_ms })
      } catch { rows.push({ name: c.name, found: 0, leak: 'ERROR', leaked: true, ms: '-' }) }
    }
    setTests(rows); setTesting(false)
  }

  const pipe = [
    { n: 1, t: 'You type', d: 'Real message stays here' },
    { n: 2, t: 'Guard scans', d: 'Finds Email, Phone, PAN, Aadhaar' },
    { n: 3, t: 'Tool sees FAKE', d: 'Outside gets tokens only' },
    { n: 4, t: 'You get REAL back', d: 'Answer restored' },
  ]

  return (
    <div className="wrap">
      <header className="hero">
        <div>
          <h1>🛡️ PII-Guard</h1>
          <p className="sub">Privacy layer for AI agents — real data never leaves your app. <b>Synthetic demo data only.</b></p>
        </div>
        <div className="status">{loading ? '⏳ Working…' : step === 4 ? '✅ Protected' : '💤 Ready'}</div>
      </header>

      <div className="pipe">
        {pipe.map((p) => (
          <div key={p.n} className={`pstep ${step >= p.n ? 'on' : ''}`}>
            <div className="dot">{step > p.n ? '✓' : p.n}</div>
            <div><b>{p.t}</b><small>{p.d}</small></div>
            {p.n < 4 && <div className="arrow">→</div>}
          </div>
        ))}
      </div>

      <section className="card">
        <h2>Step 1 — Type or pick an example</h2>
        <div className="presets">
          {Object.entries(PRESETS).map(([k, v]) => (
            <button key={k} className={input === v.text ? 'active' : ''} onClick={() => { setInput(v.text); setRes(null); setStep(1) }}>{v.label}</button>
          ))}
        </div>
        <textarea value={input} onChange={(e) => { setInput(e.target.value); setStep(1) }} rows={3} placeholder="Example: Call Ravi at 9876543210, email ravi@test.com" />
        <div className="types">
          {Object.keys(TYPE_HELP).map((t) => (
            <label key={t} title={TYPE_HELP[t]}>
              <input type="checkbox" checked={types.includes(t)} onChange={() => toggle(t)} />
              <b>{t}</b> <span>{TYPE_HELP[t]}</span>
            </label>
          ))}
        </div>
        <button className="primary" onClick={() => send()} disabled={loading}>{loading ? 'Scanning & protecting…' : '🔒 Protect & Send to Tool'}</button>
        {err && <div className="err">{err} — is backend on :8000?</div>}
      </section>

      {res && (
        <section className="card">
          <h2>Step 2 — See what happened</h2>
          <div className={`verdict ${res.leak_check === 'PASS' ? 'ok' : 'bad'}`}>
            {res.leak_check === 'PASS' ? `✅ SAFE — ${res.detections.length} private value(s) hidden. Tool got fakes only.` : '❌ LEAK — blocked.'}
            <span className="ms">{res.latency_ms} ms</span>
          </div>
          {res.detections.length === 0 && <div className="warn">No PII found. Try another example or tick all 4 boxes above.</div>}
          <div className="chips">{(res.detections || []).map((d, i) => <span key={i} className={`chip ${d.type}`}>{d.type}: {d.value}</span>)}</div>

          <div className="grid3">
            <div className="panel red">
              <h3>📝 What you typed <small>real data — stays with you</small></h3>
              <div className="txt">{highlight(res.original, res.detections, 'm-red')}</div>
            </div>
            <div className="panel yellow">
              <h3>🔌 What outside tool got <small>fake only — safe to send</small></h3>
              <div className="txt">{highlight(toText(res.tool_saw), Object.entries(res.mapping || {}).map(([tok]) => ({ value: tok })), 'm-yel')}</div>
            </div>
            <div className="panel green">
              <h3>↩️ Final answer to you <small>restored to real</small></h3>
              <div className="txt small">{highlight(toText(res.restored_response), res.detections, 'm-grn')}</div>
            </div>
          </div>

          <details>
            <summary>Fake ↔ Real list (how we restore) — click to open</summary>
            <table>
              <thead><tr><th>Fake sent out</th><th>Real kept inside</th></tr></thead>
              <tbody>{Object.entries(res.mapping || {}).map(([k, v]) => <tr key={k}><td><code>{k}</code></td><td><code>{v}</code></td></tr>)}</tbody>
            </table>
          </details>
        </section>
      )}

      <section className="card">
        <h2>Step 3 — Proof for judges</h2>
        <p className="muted">Runs 5 examples through the backend and checks: found? leaked? speed?</p>
        <button className="secondary" onClick={runTests} disabled={testing}>{testing ? 'Running…' : '▶ Run 5 tests'}</button>
        {tests && (
          <table>
            <thead><tr><th>Test</th><th>Found</th><th>Leak check</th><th>Speed</th></tr></thead>
            <tbody>{tests.map((t) => <tr key={t.name}><td>{t.name}</td><td>{t.found}</td><td>{t.leak === 'PASS' && !t.leaked ? '✅ PASS' : '❌ ' + t.leak}</td><td>{t.ms} ms</td></tr>)}</tbody>
          </table>
        )}
      </section>

      <footer>Backend <code>FastAPI :8000</code> • Frontend <code>React</code> • No real personal data used</footer>
    </div>
  )
}
