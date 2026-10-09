import { useState } from 'react'
import { I } from './icons'

export function MappingTable({ mapping, detections }) {
  const [revealed, setRevealed] = useState(false)
  const [copied, setCopied] = useState('')
  const rows = Object.entries(mapping || {})
  if (!rows.length) return <div className="empty">Nothing here yet — press “Hide privates &amp; send” first.</div>
  const typeOf = (tok) => {
    const d = (detections || []).find((x) => mapping[tok] === x.value)
    if (d) return d.type
    if (tok.includes('@')) return 'EMAIL'
    if (tok.includes('00000')) return 'PHONE'
    if (tok.startsWith('QWERT')) return 'PAN'
    if (/^(4111|5555|6011|3782)/.test(tok)) return 'CARD'
    return 'AADHAAR'
  }
  const copyTok = async (t) => {
    try { await navigator.clipboard.writeText(t); setCopied(t); setTimeout(() => setCopied(''), 1200) } catch { /* noop */ }
  }
  const mask = (v) => v.length <= 4 ? '••••' : v.slice(0, 2) + '••••' + v.slice(-2)
  return (
    <>
      <div className="toolbar" style={{ marginBottom: 6 }}>
        <button className="iconbtn" onClick={() => setRevealed((r) => !r)}>
          {revealed ? I.eyeOff({ width: 13, height: 13 }) : I.eye({ width: 13, height: 13 })}
          {revealed ? ' hide real details' : ' show real details'}
        </button>
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>Saved only in this demo — not a real safe.</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="tbl">
          <thead><tr><th>Kind</th><th>Fake (sent out)</th><th>Real (kept here)</th><th>Put back?</th></tr></thead>
          <tbody>
            {rows.map(([tok, real]) => (
              <tr key={tok}>
                <td><span className={`chip ${typeOf(tok)}`}>{typeOf(tok)}</span></td>
                <td><code>{tok}</code> <button className="iconbtn" onClick={() => copyTok(tok)}>{copied === tok ? 'copied' : 'copy'}</button></td>
                <td><code>{revealed ? real : mask(real)}</code></td>
                <td><span className="badge ok">yes</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
