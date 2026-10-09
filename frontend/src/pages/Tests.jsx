import { useState } from 'react'
import { invoke } from '../lib/api'
import { PRESETS, LIMITS } from '../lib/presets'

export function Tests({ setSuite, notify }) {
  const [rows, setRows] = useState(null)
  const [busy, setBusy] = useState(false)
  const [strict, setStrict] = useState(false)

  const run = async () => {
    setBusy(true); setRows(null)
    const cases = Object.entries(PRESETS).map(([k, v]) => ({ name: k, text: v.text }))
    const out = []
    let found = 0
    const lat = []
    for (const c of cases) {
      try {
        const d = await invoke({ text: c.text }, ['EMAIL', 'PHONE', 'PAN', 'AADHAAR', 'CARD'], strict)
        const dets = d.detections || []
        const leaked = dets.some((x) => JSON.stringify(d.tool_saw).includes(x.value))
        found += dets.length
        lat.push(d.latency_ms || 0)
        out.push({ name: c.name, found: dets.length, leak: leaked ? 'FAIL' : d.leak_check, ms: d.latency_ms, err: null })
      } catch (e) {
        out.push({ name: c.name, found: 0, leak: 'ERROR', ms: '—', err: e.message })
      }
    }
    setRows(out)
    const avg = lat.length ? (lat.reduce((a, b) => a + b, 0) / lat.length) : 0
    const p95 = lat.length ? [...lat].sort((a, b) => a - b)[Math.min(lat.length - 1, Math.floor(lat.length * 0.95))] : 0
    const leaks = out.filter((r) => r.leak !== 'PASS').length
    setSuite({ rate: out.filter((r) => r.leak === 'PASS').length * 20, found, total: found, avgMs: avg.toFixed(2), p95Ms: p95, restored: `${cases.length - leaks}/${cases.length}` })
    notify(leaks === 0 ? 'Test run complete — no leaks.' : `Test run complete — ${leaks} issue(s).`, leaks === 0 ? 'ok' : 'bad')
    setBusy(false)
  }

  return (
    <>
      <div className="card">
        <h2>Detection tests</h2>
        <p className="desc">Runs the bundled presets through the live backend. Full suite: <code>cd backend &amp;&amp; python -m pytest tests/ -q</code> (100 synthetic cases).</p>
        <div className="toolbar">
          <button className="btn primary" onClick={run} disabled={busy}>{busy ? 'Running…' : '▶ Run preset tests'}</button>
          <label className="toggle" style={{ maxWidth: 340 }}>
            <input type="checkbox" checked={strict} onChange={(e) => setStrict(e.target.checked)} />
            <span><b>Strict Aadhaar</b><small>Verhoeff checksum on</small></span>
          </label>
        </div>
        {!rows && !busy && <div className="empty" style={{ marginTop: 12 }}>No runs yet this session.</div>}
        {busy && <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}><div className="skel" /><div className="skel" /></div>}
        {rows && (
          <div style={{ overflowX: 'auto' }}>
            <table className="tbl">
              <thead><tr><th>Case</th><th>Found</th><th>Leak check</th><th>Latency</th><th>Note</th></tr></thead>
              <tbody>{rows.map((r) => (
                <tr key={r.name}><td className="mono">{r.name}</td><td>{r.found}</td>
                  <td>{r.leak === 'PASS' ? <span className="badge ok">PASS</span> : <span className="badge bad">{r.leak}</span>}</td>
                  <td className="mono">{typeof r.ms === 'number' ? `${r.ms} ms` : r.ms}</td>
                  <td style={{ color: 'var(--muted)', fontSize: 12 }}>{r.err || '—'}</td></tr>))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <h2>Known limitations</h2>
        <p className="desc">Stated honestly — this MVP does not detect every form of personal information.</p>
        <ul className="fails">{LIMITS.map((l) => <li key={l}>{l}</li>)}</ul>
      </div>
    </>
  )
}
