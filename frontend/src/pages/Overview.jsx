import { MetricCard, I } from '../components/MetricCard'
import { PrivacyPipeline } from '../components/PrivacyPipeline'

export function Overview({ activity, suite, live, phase }) {
  const runs = activity.length
  const leaks = activity.filter((a) => a.leak !== 'PASS').length
  const restored = activity.filter((a) => a.restored).length
  const avgLive = runs ? (activity.reduce((s, a) => s + (a.ms || 0), 0) / runs).toFixed(2) : null
  const det = suite ? `${suite.rate}%` : '—'
  return (
    <>
      <div className="grid4">
        <MetricCard icon={I.shield({})} label="Detection rate" value={suite ? `${suite.rate}%` : '—'}
          sub={suite ? `${suite.found}/${suite.total} values · demo sample` : 'Run Detection Tests to measure'} tone={suite ? (suite.rate >= 80 ? 'good' : 'warn') : ''} />
        <MetricCard icon={I.lock({})} label="PII leaks" value={runs ? String(leaks) : '—'}
          sub={runs ? `${runs} live invocation(s)` : 'No invocations yet'} tone={runs ? (leaks === 0 ? 'good' : 'bad') : ''} />
        <MetricCard icon={I.check({})} label="Restoration" value={runs ? `${restored}/${runs}` : '—'}
          sub={suite ? `Suite restores: ${suite.restored}` : 'Restored tool responses'} tone={runs ? (restored === runs ? 'good' : 'warn') : ''} />
        <MetricCard icon={I.pulse({})} label="Avg latency (live)" value={avgLive ? `${avgLive} ms` : '—'}
          sub={live ? `Last: ${live} ms · suite avg ${suite?.avgMs ?? '—'} ms` : 'Measured per request'} />
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h2>Chain of custody</h2>
        <p className="desc">External tools receive the released copy, never the exhibit. Markers advance only on real request state.</p>
        <PrivacyPipeline phase={phase} leak={activity[activity.length - 1]?.leak} />
        <div className="legend">
          <span><i style={{ background: 'var(--ink)' }} />redacted original</span>
          <span><i style={{ background: 'var(--amber-bg)', border: '1px dashed var(--amber)' }} />released token</span>
          <span><i style={{ background: 'transparent', borderBottom: '2px solid var(--green)' }} />declassified value</span>
        </div>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <div className="sec-title"><h2>Recent activity</h2></div>
        {runs === 0
          ? <div className="empty">File empty. Open the <a href="#agent">Agent Wiretap</a> or <a href="#playground">Redaction Desk</a> and run a case.</div>
          : <div style={{ overflowX: 'auto' }}><table className="tbl">
            <thead><tr><th>Time</th><th>Detections</th><th>Leak check</th><th>Restored</th><th>Latency</th></tr></thead>
            <tbody>{[...activity].reverse().slice(0, 8).map((a, i) => (
              <tr key={i}><td className="mono">{a.time}</td><td>{a.count}</td>
                <td>{a.leak === 'PASS' ? <span className="badge ok">PASS</span> : <span className="badge bad">{a.leak}</span>}</td>
                <td>{a.restored ? <span className="badge ok">yes</span> : <span className="badge warn">no</span>}</td>
                <td className="mono">{a.ms} ms</td></tr>))}
            </tbody></table></div>}
        <p className="desc" style={{ marginTop: 10, marginBottom: 0 }}>
          Detection {det} reflects your last demo-sample run — not a global claim. Backend suite: <code>pytest tests/</code> (100 synthetic cases).
        </p>
      </div>
    </>
  )
}
