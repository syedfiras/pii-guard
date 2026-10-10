import { useEffect, useState } from 'react'
import { apiBase, getHealth, wipeVault, getPolicy, reloadPolicy, rotateKey } from '../lib/api'

export function ApiHealth({ health, setHealth, notify }) {
  const [shredded, setShredded] = useState(null)
  const [rotated, setRotated] = useState(false)
  const [pol, setPol] = useState(null)
  const check = async () => {
    setHealth('busy')
    try { await getHealth(); setHealth('ok'); notify('Checker is running.', 'ok') }
    catch { setHealth('down'); notify('Checker is off.', 'bad') }
  }
  const shred = async () => {
    try {
      const r = await wipeVault()
      setShredded(r.wiped_tokens)
      notify(`Shredded ${r.wiped_tokens} saved mapping(s). Old fakes can never be turned back.`, 'ok')
    } catch { notify('Could not reach the checker.', 'bad') }
  }
  const rotate = async () => {
    try {
      const r = await rotateKey()
      setRotated(true)
      notify(`New lock key made, ${r.shredded_tokens} old mapping(s) shredded.`, 'ok')
    } catch { notify('Could not reach the checker.', 'bad') }
  }
  const loadPol = async (reloading) => {
    try {
      if (reloading) await reloadPolicy()
      setPol(await getPolicy())
      if (reloading) notify('Rulebook reloaded from the file.', 'ok')
    } catch { if (reloading) notify('Could not reload the rulebook.', 'bad') }
  }
  useEffect(() => { loadPol(false) }, [])
  return (
    <>
      <div className="card">
        <h2>Connection</h2>
        <p className="desc">Live status and controls.</p>
        <table className="tbl">
          <tbody>
            <tr><td>Status</td><td>{health === 'ok' ? <span className="badge ok">running</span> : health === 'busy' ? <span className="badge warn">checking…</span> : <span className="badge bad">off</span>}</td></tr>
            <tr><td>Checker address</td><td><code>{apiBase}</code></td></tr>
            <tr><td>Things the app can do</td><td><code>check message · watch agent · prove it · download proof</code></td></tr>
            <tr><td>Saved where?</td><td>Proof entries in a file on this computer; secret mappings locked in memory only</td></tr>
            <tr><td>Lock key?</td><td>Fresh secret made on every restart (or set VEIL_VAULT_KEY). Restart alone orphans all old fakes.</td></tr>
          </tbody>
        </table>
        <div className="toolbar" style={{ marginTop: 12 }}>
          <button className="btn" onClick={check}>Check again</button>
          <button className="btn primary" onClick={shred}>Shred saved mappings</button>
          <button className="btn" onClick={rotate}>Make a new lock key</button>
          {shredded !== null && <span className="badge ok">shredded {shredded}</span>}
          {rotated && <span className="badge ok">key rotated</span>}
        </div>
        <p className="desc" style={{ marginTop: 10, marginBottom: 0 }}>
          Afterwards, stolen fakes can never be turned back — not even by us.
        </p>
      </div>
      <div className="card" style={{ marginTop: 12 }}>
        <div className="sec-title">
          <h2>House rules</h2>
          <button className="btn ghost" style={{ marginLeft: 'auto', padding: '5px 12px', fontSize: 12.5 }} onClick={() => loadPol(true)}>Reload from file</button>
        </div>
        <p className="desc">What gets looked for, and what each tool may never receive.</p>
        {!pol && <div className="empty">Could not load the rulebook — is the checker running?</div>}
        {pol && (
          <div style={{ overflowX: 'auto' }}>
            <table className="tbl">
              <thead><tr><th>Detail</th><th>Looked for?</th><th>If found</th></tr></thead>
              <tbody>{Object.entries(pol.types || {}).map(([t, c]) => (
                <tr key={t}><td><span className={`chip ${t}`}>{t}</span></td>
                  <td>{c.enabled !== false ? <span className="badge ok">yes</span> : <span className="badge warn">no</span>}</td>
                  <td>{c.action === 'block' ? <span className="badge bad">refuse everything</span> : 'swap with fake'}</td></tr>))}
              </tbody>
            </table>
            <table className="tbl" style={{ marginTop: 10 }}>
              <thead><tr><th>Tool</th><th>Never allowed</th></tr></thead>
              <tbody>{Object.entries(pol.tools || {}).map(([t, c]) => (
                <tr key={t}><td className="mono">{t}</td>
                  <td>{(c.deny || []).length ? (c.deny || []).map((d) => <span key={d} className={`chip ${d}`} style={{ marginRight: 5 }}>{d}</span>) : '—'}</td></tr>))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}
