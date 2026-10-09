import { useState } from 'react'
import { invoke, toText } from '../lib/api'
import { PRESETS, TYPE_HELP } from '../lib/presets'
import { I } from '../components/icons'
import { PrivacyPipeline } from '../components/PrivacyPipeline'
import { ComparisonPanel } from '../components/ComparisonPanel'
import { MappingTable } from '../components/MappingTable'

export function Playground({ pushActivity, notify, setPhase }) {
  const [input, setInput] = useState(PRESETS.all.text)
  const [format, setFormat] = useState('text')
  const [types, setTypes] = useState(['EMAIL', 'PHONE', 'PAN', 'AADHAAR', 'CARD'])
  const [strict, setStrict] = useState(false)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [res, setRes] = useState(null)
  const [original, setOriginal] = useState('')

  const toggle = (t) => setTypes((p) => p.includes(t) ? p.filter((x) => x !== t) : [...p, t])

  const send = async () => {
    const text = input.trim()
    if (!text) { setErr('Type a message or pick a preset first.'); return }
    let payload
    if (format === 'json') {
      try { payload = JSON.parse(text) }
      catch { setErr('Invalid JSON — check syntax or switch to Text mode.'); return }
    } else payload = { text }
    setLoading(true); setErr(''); setPhase(1)
    try {
      const data = await invoke(payload, types, strict)
      if (data.blocked || data.error) throw new Error(data.error || 'Request blocked by leak check.')
      const orig = format === 'json' ? JSON.stringify(payload, null, 2) : payload.text
      setOriginal(orig); setRes(data); setPhase(2)
      const dets = data.detections || []
      const restoredOk = JSON.stringify(data.restored_response || '').length > 0
      pushActivity({ time: new Date().toLocaleTimeString(), count: dets.length, leak: data.leak_check, restored: restoredOk, ms: data.latency_ms })
      notify(data.leak_check === 'PASS' ? `Safe — hid ${dets.length} private detail(s).` : 'Leak found — sending blocked.', data.leak_check === 'PASS' ? 'ok' : 'bad')
    } catch (e) {
      setErr(e.message.includes('Failed to fetch') ? 'Checker is off. Run start.bat, or in backend: python -m uvicorn app:app --port 8000' : e.message)
      setPhase(0); notify('Request failed.', 'bad')
    } finally { setLoading(false) }
  }

  const dets = res?.detections || []
  const tokens = Object.keys(res?.mapping || {})
  const toolText = res ? toText(res.tool_saw ?? res.redacted_payload) : ''
  const restoredText = res ? toText(res.restored_response) : ''

  return (
    <>
      <PrivacyPipeline phase={loading ? 1 : res ? 2 : 0} leak={res?.leak_check} />
      <div className="grid2" style={{ marginTop: 12 }}>
        <div className="card">
          <h2>Your message</h2>
          <p className="desc">What you type here is only shown to you. <span className="badge warn">fake data only</span></p>
          <div className="toolbar" style={{ marginBottom: 10 }}>
            <div className="presets">
              {Object.entries(PRESETS).map(([k, v]) => (
                <button key={k} className={`btn ghost ${input === v.text ? 'on' : ''}`} style={{ padding: '6px 11px', fontSize: 12.5 }}
                  onClick={() => { setInput(v.text); setFormat('text'); setRes(null); setPhase(0) }}>{v.label}</button>
              ))}
            </div>
          </div>
          <div className="toolbar" style={{ marginBottom: 8 }}>
            <button className={`btn ghost ${format === 'text' ? 'on' : ''}`} style={{ padding: '6px 11px', fontSize: 12.5 }} onClick={() => setFormat('text')}>Text</button>
            <button className={`btn ghost ${format === 'json' ? 'on' : ''}`} style={{ padding: '6px 11px', fontSize: 12.5 }} onClick={() => setFormat('json')}>JSON</button>
            <button className="btn ghost" style={{ padding: '6px 11px', fontSize: 12.5 }} onClick={() => { setInput(''); setRes(null); setPhase(0) }}>Reset</button>
          </div>
          <textarea className="editor" rows={5} value={input} onChange={(e) => setInput(e.target.value)}
            placeholder={format === 'json' ? '{"message": "Call Ravi at 9876543210"}' : 'Example: Contact user_0001@example.test at +91-98765-43210 regarding verification.'} />
          <div className="toggles" style={{ marginTop: 10 }}>
            {Object.entries(TYPE_HELP).map(([t, h]) => (
              <label key={t} className="toggle" title={h}>
                <input type="checkbox" checked={types.includes(t)} onChange={() => toggle(t)} />
                <span><b>{t}</b><small>{h}</small></span>
              </label>
            ))}
          </div>
          <label className="toggle" style={{ marginTop: 8, borderColor: 'rgba(245,158,11,.4)' }}>
            <input type="checkbox" checked={strict} onChange={(e) => setStrict(e.target.checked)} />
            <span><b>Strict ID check</b><small>OFF = catches more, may over-catch · ON = double-checks ID numbers</small></span>
          </label>
          <button className="btn primary" style={{ width: '100%', justifyContent: 'center', marginTop: 10 }} onClick={send} disabled={loading}>
            {I.send({ width: 15, height: 15 })} {loading ? 'Hiding…' : 'Hide privates & send'}
          </button>
          {err && <div className="err" style={{ marginTop: 10 }}>{err}</div>}
        </div>

        <div className="card">
          <h2>What we found</h2>
          <p className="desc">These came from the checker program — nothing typed by hand.</p>
          {!res && !loading && <div className="empty">Press “Hide privates &amp; send” to see what is found.</div>}
          {loading && <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}><div className="skel" /><div className="skel" /><div className="skel" /></div>}
          {res && (
            <>
              <div className={`verdict ${res.leak_check === 'PASS' ? 'ok' : 'bad'}`}>
                {res.leak_check === 'PASS' ? `Safe — hid ${dets.length} private detail(s).` : 'Leak found — sending blocked.'}
                <span className="ms">{res.latency_ms} ms</span>
              </div>
              {dets.length === 0
                ? <div className="empty">Nothing private found with these boxes ticked. Try another example.</div>
                : <div className="chips" style={{ marginTop: 10 }}>{dets.map((d, i) => <span key={i} className={`chip ${d.type}`}>{d.type} · {d.value}</span>)}</div>}
              <div className="legend" style={{ marginTop: 10 }}>
                <span><i style={{ background: 'var(--ink)' }} />hidden</span>
                <span><i style={{ background: 'var(--amber-bg)', border: '1px dashed var(--amber)' }} />fake</span>
                <span><i style={{ background: 'transparent', borderBottom: '2px solid var(--green)' }} />given back</span>
              </div>
              <div style={{ marginTop: 10 }}><a href="#logs" className="btn ghost" style={{ fontSize: 13, textDecoration: 'none' }}>See the proof log →</a></div>
            </>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h2>Side by side</h2>
        <p className="desc">Your message, what the tool got, and what you got back — all from the live checker.</p>
        {!res && <div className="empty">Three boxes appear here after it runs.</div>}
        {res && (
          <div className="grid3">
            <ComparisonPanel title="1 · Your message" sub="only you see this" tone="#b3271e"
              body={original} values={dets.map((d) => d.value)} markCls="m-red" empty="—" />
            <ComparisonPanel title="2 · What the tool got" sub={res.leak_check === 'PASS' ? 'only fakes · check: safe' : 'check: leaked!'} tone="#8a5f00"
              body={toolText} values={tokens} markCls="m-yel" empty="—" />
            <ComparisonPanel title="3 · What you got back" sub="fakes changed back to real" tone="#1e6b3a"
              body={restoredText} values={dets.map((d) => d.value)} markCls="m-grn" empty="—" />
          </div>
        )}
      </div>

      {res && (
        <div className="card" style={{ marginTop: 12 }}>
          <h2>What replaced what</h2>
          <p className="desc">Kept only in this demo. Real details are hidden unless you press show.</p>
          <MappingTable mapping={res.mapping} detections={dets} />
        </div>
      )}
    </>
  )
}
