import { useState } from 'react'
import { agentChat, toText } from '../lib/api'
import { I } from '../components/icons'

const STARTERS = [
  'My card 4111 1111 1111 1111 did not get the OTP. I am at 9876543210, email ravi@test.com. Please send it again.',
  'Book my checkup. Aadhaar 2344 5678 9012, call me on +91-98765 43210 to confirm.',
  'Send my KYC to the officer: PAN BNZPM5678K, priya.sharma@test.com.',
]

export function AgentDemo({ pushActivity, notify, setPhase }) {
  const [guard, setGuard] = useState(true)
  const [msgs, setMsgs] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [last, setLast] = useState(null)
  const [err, setErr] = useState('')

  const ask = async (text) => {
    const q = (text ?? draft).trim()
    if (!q || busy) return
    setDraft(''); setErr(''); setBusy(true); setPhase(1)
    setMsgs((m) => [...m, { who: 'you', text: q }])
    try {
      const d = await agentChat(q, guard)
      if (d.error) throw new Error(d.error)
      setMsgs((m) => [...m, { who: 'agent', text: d.reply }])
      setLast(d); setPhase(2)
      ;(d.trace || []).forEach((t) => pushActivity({
        time: new Date().toLocaleTimeString(),
        count: (t.detections || []).length,
        leak: t.leak_check === 'PASS' ? 'PASS' : 'FAIL',
        restored: guard, ms: d.latency_ms,
      }))
      const bad = (d.trace || []).some((t) => t.leak_check !== 'PASS')
      notify(bad ? 'Warning: the tool saw real details!' : `Done — ${(d.trace || []).length} tool use(s), all with fakes.`, bad ? 'bad' : 'ok')
    } catch (e) {
      setErr(e.message.includes('Failed to fetch') ? 'Checker is off. Run start.bat, or in backend: python -m uvicorn app:app --port 8000' : e.message)
      setPhase(0)
    } finally { setBusy(false) }
  }

  const leaked = last && (last.trace || []).some((t) => t.leak_check !== 'PASS')

  return (
    <>
      <div className="card">
        <h2>Watch the agent</h2>
        <p className="desc">
          Talk to the demo bank helper. It uses tools <i>by itself, without asking you</i> — below you can see
          what each tool really got. Turn protection off to see what happens without us.
        </p>
        <div className="toolbar" style={{ marginBottom: 10 }}>
          <button className={`guardswitch ${guard ? 'on' : 'off'}`} onClick={() => setGuard((g) => !g)} aria-pressed={guard}>
            {guard ? 'Protection: ON — everything passes through us first' : 'Protection: OFF — agent talks to tools directly'}
          </button>
        </div>
        <div className="toolbar" style={{ marginBottom: 10 }}>
          {STARTERS.map((s, i) => (
            <button key={i} className="btn ghost" style={{ fontSize: 12.5 }} onClick={() => ask(s)} disabled={busy}>
              Case {i + 1}: {s.slice(0, 42)}…
            </button>
          ))}
        </div>
        <div className="chatlog" aria-live="polite">
          {msgs.length === 0 && <div className="empty">No chat yet. Tap an example above or type below.</div>}
          {msgs.map((m, i) => (
            <div key={i} className={`bubble ${m.who === 'you' ? 'user' : 'agent'}`}>
              <span className="who">{m.who === 'you' ? 'you' : 'bank helper (demo)'}</span>
              {m.text}
            </div>
          ))}
          {busy && <div className="bubble agent"><span className="who">agent</span><span className="skel" style={{ display: 'block' }}>…</span></div>}
        </div>
        <div className="toolbar" style={{ marginTop: 10 }}>
          <input className="search" style={{ flex: 1 }} value={draft} onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && ask()} placeholder="Pretend you are the customer — include phone, card, etc…" />
          <button className="btn primary" onClick={() => ask()} disabled={busy}>{I.send({ width: 14, height: 14 })} Send</button>
        </div>
        {err && <div className="err" style={{ marginTop: 10 }}>{err}</div>}
      </div>

      {last && (
        <div className="card" style={{ marginTop: 12 }}>
          <h2>Behind the scenes — what the tools got ({(last.trace || []).length})</h2>
          {leaked
            ? <div className="verdict bad">Leak! Real details reached the tool<span className="ms">{last.latency_ms} ms</span></div>
            : <div className="verdict ok">Safe — tools only saw fakes<span className="ms">{last.latency_ms} ms</span></div>}
          {(last.trace || []).map((t, i) => (
            <div className="trace" key={i}>
              <header>
                Tool use {i + 1} · <span className="mono">{t.tool}</span>
                <span style={{ marginLeft: 'auto' }}>
                  {t.leak_check === 'PASS' ? <span className="badge ok">safe</span> : <span className="badge bad">leaked</span>}
                </span>
              </header>
              <div className="tsec">
                <h4>Helper tried to send (your real details)</h4>
                <pre>{toText(t.attempted)}</pre>
              </div>
              <div className="tsec">
                <h4>Tool really got {t.leak_check === 'PASS' ? '(fakes)' : '(REAL — leaked!)'}</h4>
                <pre>{toText(t.sent)}</pre>
              </div>
              {(t.detections || []).length > 0 && (
                <div className="tsec">
                  <h4>Hidden this time</h4>
                  <div className="chips">{t.detections.map((d, j) => <span key={j} className={`chip ${d.type}`}>{d.type} · {d.value}</span>)}</div>
                </div>
              )}
            </div>
          ))}
          <p className="desc" style={{ marginTop: 10, marginBottom: 0 }}>
            Protection was {last.guard ? 'ON' : 'OFF'} for this chat. OFF still uses the pretend tool — it only shows what would happen with no protection.
          </p>
        </div>
      )}
    </>
  )
}
