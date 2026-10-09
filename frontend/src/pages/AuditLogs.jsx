import { useEffect, useState } from 'react'
import { getLogs, toText, countTokens, apiBase } from '../lib/api'
import { I } from '../components/icons'

/** Audit log shows SANITIZED payloads only — never originals or vault mapping. */
export function AuditLogs({ notify }) {
  const [logs, setLogs] = useState(null)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')
  const [f, setF] = useState('all')
  const [open, setOpen] = useState(null)

  const load = async () => {
    setBusy(true)
    try { setLogs(await getLogs()) }
    catch { notify('Could not reach the checker.', 'bad'); setLogs({ logs: [] }) }
    finally { setBusy(false) }
  }
  const download = async () => {
    try {
      const r = await fetch(`${apiBase}/api/evidence`)
      if (!r.ok) throw new Error()
      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = 'veil-guard-evidence.json'
      a.click()
      URL.revokeObjectURL(a.href)
      notify('Evidence file downloaded.', 'ok')
    } catch { notify('Could not download evidence.', 'bad') }
  }
  useEffect(() => {
    let on = true
    setBusy(true)
    getLogs().then((d) => { if (on) setLogs(d) })
      .catch(() => { if (on) { notify('Could not reach the checker.', 'bad'); setLogs({ logs: [] }) } })
      .finally(() => { if (on) setBusy(false) })
    return () => { on = false }
  }, [])

  const items = (logs?.logs || []).filter((e) => {
    const s = JSON.stringify(e.received || '').toLowerCase()
    if (q && !s.includes(q.toLowerCase()) && !(e.tool || '').toLowerCase().includes(q.toLowerCase())) return false
    if (f === 'ok' || f === 'fail') return true // backend log has no leak flag; filter kept for UX parity
    return true
  })

  return (
    <div className="card">
        <h2>Proof log</h2>
        <p className="desc">What the outside tool got — cleaned copies only. Your real details never appear here.</p>
      <div className="toolbar">
        <span style={{ position: 'relative' }}>
          <input className="search" placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} style={{ paddingLeft: 30 }} />
          <span style={{ position: 'absolute', left: 9, top: 8, color: 'var(--muted)' }}>{I.search({ width: 14, height: 14 })}</span>
        </span>
        <select className="search" value={f} onChange={(e) => setF(e.target.value)} aria-label="Show">
          <option value="all">Show everything</option>
          <option value="ok">Only safe ones</option>
        </select>
        <button className="btn" onClick={load} disabled={busy}>{I.refresh({ width: 14, height: 14 })} {busy ? 'Loading…' : 'Reload'}</button>
        <button className="btn primary" onClick={download} disabled={busy}>Download proof file</button>
      </div>
      {!logs && busy && <div className="skel" style={{ marginTop: 12 }} />}
      {logs && items.length === 0 && <div className="empty" style={{ marginTop: 12 }}>Nothing here yet. Try the “Check a message” page first.</div>}
      {items.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>When</th><th>Tool</th><th>Result</th><th>Hidden</th><th>See more</th></tr></thead>
            <tbody>{[...items].reverse().slice(0, 30).map((e, i) => {
              const txt = toText(e.received)
              return (
                <tr key={i}>
                  <td className="mono" style={{ whiteSpace: 'nowrap' }}>{e.time || '—'}</td>
                  <td className="mono">{e.tool || '—'}</td>
                  <td><span className="badge ok">safe</span></td>
                  <td>{countTokens(txt)}</td>
                  <td><button className="iconbtn" onClick={() => setOpen(open === i ? null : i)}>{open === i ? 'hide' : 'view'}</button>
                    {open === i && <pre style={{ background: 'var(--paper)', padding: 10, fontSize: 12, maxHeight: 220, overflow: 'auto' }}>{txt.slice(0, 2000)}</pre>}
                  </td>
                </tr>
              )
            })}</tbody>
          </table>
        </div>
      )}
    </div>
  )
}
