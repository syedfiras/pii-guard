import { apiBase, getHealth } from '../lib/api'

export function ApiHealth({ health, setHealth, notify }) {
  const check = async () => {
    setHealth('busy')
    try { await getHealth(); setHealth('ok'); notify('Backend connected.', 'ok') }
    catch { setHealth('down'); notify('Backend unreachable.', 'bad') }
  }
  return (
    <div className="card">
      <h2>API health &amp; configuration</h2>
      <p className="desc">Live status from <code>GET /api/health</code>. No invented capabilities.</p>
      <table className="tbl">
        <tbody>
          <tr><td>Status</td><td>{health === 'ok' ? <span className="badge ok">connected</span> : health === 'busy' ? <span className="badge warn">checking…</span> : <span className="badge bad">disconnected</span>}</td></tr>
          <tr><td>API base URL</td><td><code>{apiBase}</code> <span style={{ color: 'var(--muted)', fontSize: 12 }}>(VITE_API_URL or default)</span></td></tr>
          <tr><td>Contracts</td><td><code>/api/invoke · /api/agent/chat · /api/restore · /api/tool-logs · /api/health</code></td></tr>
          <tr><td>Storage</td><td>in-memory vault + log (no database, per PRD non-goals)</td></tr>
        </tbody>
      </table>
      <div className="toolbar" style={{ marginTop: 12 }}>
        <button className="btn" onClick={check}>Retry health check</button>
      </div>
    </div>
  )
}
