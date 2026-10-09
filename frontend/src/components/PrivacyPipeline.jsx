import { I } from './icons'

const STEPS = [
  { key: 'input', icon: 'flask', t: 'You type', d: 'Your message stays here' },
  { key: 'detect', icon: 'shield', t: 'We hide it', d: 'Private parts become fakes' },
  { key: 'tool', icon: 'send', t: 'Tool gets fakes', d: 'Your real message never leaves' },
  { key: 'restore', icon: 'check', t: 'You get it back', d: 'Fakes turned back to real' },
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
                ? (leak === 'PASS' ? <span className="badge ok">safe</span> : <span className="badge bad">leaked</span>)
                : phase === 1 && i === 1 ? <span className="badge warn">working</span> : null}
            </span>
          </div>
        )
      })}
    </div>
  )
}
