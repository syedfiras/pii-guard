import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { getHealth } from './lib/api'
import { Sidebar, Topbar, MobileNav, Toasts } from './components/Shell'
import { Overview } from './pages/Overview'
import { Playground } from './pages/Playground'
import { AgentDemo } from './pages/AgentDemo'
import { Tests } from './pages/Tests'
import { AuditLogs } from './pages/AuditLogs'
import { ApiHealth } from './pages/ApiHealth'

const TITLES = {
  '#overview': ['Overview', 'Live protection status, chain of custody and recent activity.'],
  '#playground': ['Redaction Desk', 'Type a message, redact it, and compare against what the tool saw.'],
  '#agent': ['Agent Wiretap', 'The agent calls tools behind your back. Watch the wire.'],
  '#tests': ['Detection Tests', 'Run the bundled demo sample through the live backend.'],
  '#logs': ['Audit Logs', 'Sanitized payloads the simulated tool received — no originals.'],
  '#health': ['API Health', 'Backend connection and configuration.'],
}
const tick = () => window.location.hash || '#overview'

export default function App() {
  const [route, setRoute] = useState(tick())
  const [health, setHealth] = useState('busy')
  const [activity, setActivity] = useState([])
  const [suite, setSuite] = useState(null)
  const [live, setLive] = useState(null)
  const [phase, setPhase] = useState(0)
  const [toasts, setToasts] = useState([])

  const notify = useCallback((text, kind) => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, text, kind }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200)
  }, [])

  const check = useCallback(async () => {
    setHealth('busy')
    try { await getHealth(); setHealth('ok') } catch { setHealth('down') }
  }, [])

  useEffect(() => {
    check()
    const onH = () => setRoute(tick())
    window.addEventListener('hashchange', onH)
    if (!window.location.hash) window.location.hash = '#overview'
    return () => window.removeEventListener('hashchange', onH)
  }, [check])

  const pushActivity = useCallback((a) => {
    setActivity((prev) => [...prev.slice(-19), a])
    setLive(a.ms)
  }, [])

  const [title, desc] = TITLES[route] || TITLES['#overview']

  return (
    <div className="shell">
      <Sidebar route={route} health={health} />
      <div className="main">
        <Topbar title={title} desc={desc} health={health} onRetry={check} />
        <MobileNav route={route} />
        <div className="content">
          {route === '#overview' && <Overview activity={activity} suite={suite} live={live} phase={phase} />}
          {route === '#playground' && <Playground pushActivity={pushActivity} notify={notify} setPhase={setPhase} />}
          {route === '#agent' && <AgentDemo pushActivity={pushActivity} notify={notify} setPhase={setPhase} />}
          {route === '#tests' && <Tests setSuite={setSuite} notify={notify} />}
          {route === '#logs' && <AuditLogs notify={notify} />}
          {route === '#health' && <ApiHealth health={health} setHealth={setHealth} notify={notify} />}
        </div>
      </div>
      <Toasts items={toasts} />
    </div>
  )
}
