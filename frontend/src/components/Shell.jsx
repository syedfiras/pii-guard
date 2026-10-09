import { I } from './icons'

const NAV = [
  { h: '#overview', label: 'Overview', icon: 'grid' },
  { h: '#playground', label: 'Redaction Desk', icon: 'flask' },
  { h: '#agent', label: 'Agent Wiretap', icon: 'send' },
  { h: '#tests', label: 'Detection Tests', icon: 'list' },
  { h: '#logs', label: 'Audit Logs', icon: 'pulse' },
  { h: '#health', label: 'API Health', icon: 'gear' },
]

export function Sidebar({ route, health }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">{I.shield({ width: 19, height: 19 })}</div>
        <div><b>PII-Guard</b><small>case file no. 001 · mvp</small></div>
      </div>
      <nav className="nav" aria-label="Primary">
        {NAV.map((n) => (
          <a key={n.h} href={n.h} className={route === n.h ? 'on' : ''}>
            {I[n.icon]?.({})}<span>{n.label}</span>
          </a>
        ))}
      </nav>
      <div className="side-foot">
        <div className="pill"><span className={`dot ${health === 'ok' ? 'ok' : health === 'busy' ? 'busy' : 'bad'}`} />
          {health === 'ok' ? 'Backend connected' : health === 'busy' ? 'Checking backend…' : 'Backend offline'}</div>
        <div className="pill">{I.lock({ width: 13, height: 13 })} Local demo · synthetic data</div>
      </div>
    </aside>
  )
}

export function Topbar({ title, desc, health, onRetry }) {
  return (
    <div className="topbar">
      <div>
        <h1>{title}</h1>
        <p>{desc}</p>
      </div>
      <div className="top-right">
        <span className="tag synth">demo file · synthetic data</span>
        <span className="tag" title="Backend /api/health">
          <span className={`dot ${health === 'ok' ? 'ok' : health === 'busy' ? 'busy' : 'bad'}`} style={{ display: 'inline-block', marginRight: 6 }} />
          {health === 'ok' ? 'connected' : health === 'busy' ? 'checking…' : 'disconnected'}
        </span>
        {health !== 'ok' && <button className="btn ghost" onClick={onRetry} style={{ padding: '6px 11px', fontSize: 12 }}>retry</button>}
      </div>
    </div>
  )
}

export function MobileNav({ route }) {
  return (
    <div className="mobilenav">
      {NAV.map((n) => <a key={n.h} href={n.h} className={route === n.h ? 'on' : ''}>{n.label}</a>)}
    </div>
  )
}

export function Toasts({ items }) {
  return (
    <div className="toasts" aria-live="polite">
      {items.map((t) => (
        <div key={t.id} className={`toast ${t.kind || ''}`}>
          {t.kind === 'ok' ? I.check({ width: 15, height: 15 }) : I.warn({ width: 15, height: 15 })}
          <span>{t.text}</span>
        </div>
      ))}
    </div>
  )
}
