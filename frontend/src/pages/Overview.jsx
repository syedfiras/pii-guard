import { useState } from 'react'
import { MetricCard, I } from '../components/MetricCard'
import { PrivacyPipeline } from '../components/PrivacyPipeline'

export function Overview({ activity, suite, live, phase, onDeleteRow, onClearAll }) {
  const [confirming, setConfirming] = useState(false)
  const runs = activity.length
  const leaks = activity.filter((a) => a.leak !== 'PASS').length
  const restored = activity.filter((a) => a.restored).length
  const avgLive = runs ? (activity.reduce((s, a) => s + (a.ms || 0), 0) / runs).toFixed(2) : null
  const realIdx = (revIdx) => activity.length - 1 - revIdx
  return (
    <>
      <div className="grid4">
        <MetricCard icon={I.shield({})} label="Caught" value={suite ? `${suite.rate}%` : '—'}
          sub={suite ? `${suite.found}/${suite.total} hidden · test run` : 'Run the tests page to measure'} tone={suite ? (suite.rate >= 80 ? 'good' : 'warn') : ''} />
        <MetricCard icon={I.lock({})} label="Leaks" value={runs ? String(leaks) : '—'}
          sub={runs ? `across ${runs} use(s)` : 'Nothing used yet'} tone={runs ? (leaks === 0 ? 'good' : 'bad') : ''} />
        <MetricCard icon={I.check({})} label="Given back correctly" value={runs ? `${restored}/${runs}` : '—'}
          sub={suite ? `Tests gave back: ${suite.restored}` : 'Answers with originals put back'} tone={runs ? (restored === runs ? 'good' : 'warn') : ''} />
        <MetricCard icon={I.pulse({})} label="Speed" value={avgLive ? `${avgLive} ms` : '—'}
          sub={live ? `Last one: ${live} ms` : 'Time added per check'} />
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h2>How your data travels</h2>
        <p className="desc">Outside tools only get the fake copy — never your real message. The steps light up only during a real check.</p>
        <PrivacyPipeline phase={phase} leak={activity[activity.length - 1]?.leak} />
        <div className="legend">
          <span><i style={{ background: 'var(--ink)' }} />hidden original</span>
          <span><i style={{ background: 'var(--amber-bg)', border: '1px dashed var(--amber)' }} />fake copy</span>
          <span><i style={{ background: 'transparent', borderBottom: '2px solid var(--green)' }} />given back</span>
        </div>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <div className="sec-title">
          <h2>Past checks</h2>
          {runs > 0 && (
            confirming
              ? <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                  <span style={{ fontSize: 13, alignSelf: 'center' }}>Delete everything?</span>
                  <button className="btn" style={{ padding: '5px 12px', fontSize: 12.5 }} onClick={() => { onClearAll(); setConfirming(false) }}>Yes, delete</button>
                  <button className="btn ghost" style={{ padding: '5px 12px', fontSize: 12.5 }} onClick={() => setConfirming(false)}>Keep</button>
                </span>
              : <button className="btn ghost" style={{ marginLeft: 'auto', padding: '5px 12px', fontSize: 12.5 }} onClick={() => setConfirming(true)}>Delete history</button>
          )}
        </div>
        <p className="desc">Saved on this computer only — it stays even after refresh. Only counts are saved, never your messages.</p>
        {runs === 0
          ? <div className="empty">Nothing here yet. Open <a href="#agent">Watch the agent</a> or <a href="#playground">Check a message</a> and run something.</div>
          : <div style={{ overflowX: 'auto' }}><table className="tbl">
            <thead><tr><th>Time</th><th>Hidden</th><th>Leak?</th><th>Given back</th><th>Speed</th><th></th></tr></thead>
            <tbody>{[...activity].reverse().slice(0, 10).map((a, i) => (
              <tr key={i}><td className="mono">{a.time}</td><td>{a.count}</td>
                <td>{a.leak === 'PASS' ? <span className="badge ok">safe</span> : <span className="badge bad">leaked</span>}</td>
                <td>{a.restored ? <span className="badge ok">yes</span> : <span className="badge warn">no</span>}</td>
                <td className="mono">{a.ms} ms</td>
                <td><button className="iconbtn" aria-label="Delete this row" onClick={() => onDeleteRow(realIdx(i))}>delete</button></td></tr>))}
            </tbody></table></div>}
      </div>
    </>
  )
}
