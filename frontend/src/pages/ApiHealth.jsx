import { apiBase, getHealth } from '../lib/api'

export function ApiHealth({ health, setHealth, notify }) {
  const check = async () => {
    setHealth('busy')
    try { await getHealth(); setHealth('ok'); notify('Checker is running.', 'ok') }
    catch { setHealth('down'); notify('Checker is off.', 'bad') }
  }
  return (
    <div className="card">
      <h2>Connection</h2>
      <p className="desc">Is the checker program running right now? Checked live — nothing made up.</p>
      <table className="tbl">
        <tbody>
          <tr><td>Status</td><td>{health === 'ok' ? <span className="badge ok">running</span> : health === 'busy' ? <span className="badge warn">checking…</span> : <span className="badge bad">off</span>}</td></tr>
          <tr><td>Checker address</td><td><code>{apiBase}</code></td></tr>
          <tr><td>Things the app can do</td><td><code>check message · watch agent · prove it · download proof</code></td></tr>
          <tr><td>Saved where?</td><td>Proof entries in a file on this computer; secret mappings in memory only</td></tr>
        </tbody>
      </table>
      <div className="toolbar" style={{ marginTop: 12 }}>
        <button className="btn" onClick={check}>Check again</button>
      </div>
    </div>
  )
}
