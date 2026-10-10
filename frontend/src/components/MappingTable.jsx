import { useState } from 'react'
import { I } from './icons'
import { revealTokens } from '../lib/api'

/* Real details are NEVER in this table until you press show — then each
   reveal is fetched from the server one by one, and every fetch is logged. */
export function MappingTable({ mapping, detections, sessionId, notify }) {
  const [revealed, setRevealed] = useState(null) // {token: real} or null
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState('')
  const rows = Object.entries(mapping || {})
  if (!rows.length) return <div className="empty">Nothing here yet — press “Hide privates &amp; send” first.</div>
  const typeOf = (tok) => {
    const m = tok.match(/^__([A-Z_]+)_[0-9a-f]+__$/)
    if (m) return m[1]
    if (tok.includes('@')) return 'EMAIL'
    if (/^\+91-0/.test(tok)) return 'PHONE'
    if (tok.startsWith('QWERT')) return 'PAN'
    if (/^(4111|5555|6011|3782)/.test(tok)) return 'CARD'
    return 'AADHAAR'
  }
  const show = async () => {
    if (revealed) { setRevealed(null); return }
    setBusy(true)
    try {
      const r = await revealTokens(sessionId, rows.map(([t]) => t))
      setRevealed(r.revealed || {})
      notify && notify('Each view is written to the proof log.', 'ok')
    } catch { notify && notify('Could not fetch details.', 'bad') }
    finally { setBusy(false) }
  }
  const copyTok = async (t) => {
    try { await navigator.clipboard.writeText(t); setCopied(t); setTimeout(() => setCopied(''), 1200) } catch { /* noop */ }
  }
  const shown = (tok) => (revealed && revealed[tok]) || rows.find(([t]) => t === tok)[1]
  return (
    <>
      <div className="toolbar" style={{ marginBottom: 6 }}>
        <button className="iconbtn" onClick={show} disabled={busy}>
          {revealed ? I.eyeOff({ width: 13, height: 13 }) : I.eye({ width: 13, height: 13 })}
          {busy ? ' asking…' : revealed ? ' hide real details' : ' show real details'}
        </button>
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>Saved locked on the checker. Showing them here writes a note in the proof log.</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="tbl">
          <thead><tr><th>Kind</th><th>Fake (sent out)</th><th>Real (kept here)</th><th>Put back?</th></tr></thead>
          <tbody>
            {rows.map(([tok]) => (
              <tr key={tok}>
                <td><span className={`chip ${typeOf(tok)}`}>{typeOf(tok)}</span></td>
                <td><code>{tok}</code> <button className="iconbtn" onClick={() => copyTok(tok)}>{copied === tok ? 'copied' : 'copy'}</button></td>
                <td><code>{shown(tok)}</code></td>
                <td><span className="badge ok">yes</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
