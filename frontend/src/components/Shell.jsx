import { I } from './icons'

const NAV = [
  { h: '#overview', label: 'Overview', icon: 'grid' },
  { h: '#playground', label: 'Check a message', icon: 'flask' },
  { h: '#agent', label: 'Watch the agent', icon: 'send' },
  { h: '#tests', label: 'Test results', icon: 'list' },
  { h: '#logs', label: 'Proof log', icon: 'pulse' },
  { h: '#health', label: 'Connection', icon: 'gear' },
]

export function Sidebar({ route, health }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">{I.shield({ width: 19, height: 19 })}</div>
        <div><b>Veil Guard</b><small>privacy demo</small></div>
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
          {health === 'ok' ? 'Checker is running' : health === 'busy' ? 'Checking…' : 'Checker is off'}</div>
        <div className="pill">{I.lock({ width: 13, height: 13 })} Demo only · fake data</div>
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
        <span className="tag synth">demo · fake data</span>
        <span className="tag" title="Is the checker program running?">
          <span className={`dot ${health === 'ok' ? 'ok' : health === 'busy' ? 'busy' : 'bad'}`} style={{ display: 'inline-block', marginRight: 6 }} />
          {health === 'ok' ? 'running' : health === 'busy' ? 'checking…' : 'off'}
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
