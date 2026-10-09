import { I } from './icons'

const STEPS = [
  { key: 'input', icon: 'flask', t: 'Exhibit A', d: 'Raw message, stays inside' },
  { key: 'detect', icon: 'shield', t: 'Redaction desk', d: 'PII swapped for tokens' },
  { key: 'tool', icon: 'send', t: 'Released copy', d: 'Tool sees fakes only' },
  { key: 'restore', icon: 'check', t: 'Declassified', d: 'Tokens mapped back' },
]

/** phase: 0 idle, 1 sending, 2 done. protected: bool|null */
export function PrivacyPipeline({ phase, leak }) {
  return (
    <div className="pipe" role="list" aria-label="Privacy pipeline">
      {STEPS.map((s, i) => {
        const active = phase === 1 && i <= 1
        const done = phase === 2
        return (
          <div key={s.key} role="listitem" className={`pstep ${active ? 'active' : ''} ${done ? 'done' : ''}`}>
            <div className="ic">{I[s.icon]?.({})}</div>
            <b>{s.t}</b>
            <small>{s.d}</small>
            <span className="st">
              {phase === 2 && i === 3
                ? (leak === 'PASS' ? <span className="badge ok">protected</span> : <span className="badge bad">blocked</span>)
                : phase === 1 && i === 1 ? <span className="badge warn">scanning</span> : null}
            </span>
          </div>
        )
      })}
    </div>
  )
}
