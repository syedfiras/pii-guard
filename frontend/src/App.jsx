import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { getHealth } from './lib/api'
import { loadHistory, saveHistory, clearHistory } from './lib/storage'
import { Sidebar, Topbar, MobileNav, Toasts } from './components/Shell'
import { Overview } from './pages/Overview'
import { Playground } from './pages/Playground'
import { AgentDemo } from './pages/AgentDemo'
import { Tests } from './pages/Tests'
import { AuditLogs } from './pages/AuditLogs'
import { ApiHealth } from './pages/ApiHealth'

const TITLES = {
  '#overview': ['Overview', 'Your protection at a glance.'],
  '#playground': ['Check a message', 'See what gets hidden before anything is sent.'],
  '#agent': ['Watch the agent', 'See what the helper really sends to its tools.'],
  '#tests': ['Test results', 'Ready-made examples, checked live.'],
  '#logs': ['Proof log', 'Copies of what outside tools received.'],
  '#health': ['Connection', 'Status, rules and controls.'],
}
const tick = () => window.location.hash || '#overview'

export default function App() {
  const [route, setRoute] = useState(tick())
  const [health, setHealth] = useState('busy')
  const [activity, setActivity] = useState(() => loadHistory().activity)
  const [suite, setSuite] = useState(() => loadHistory().suite)
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

  useEffect(() => {
    saveHistory(activity, suite)
  }, [activity, suite])

  const pushActivity = useCallback((a) => {
    setActivity((prev) => [...prev.slice(-29), a])
    setLive(a.ms)
  }, [])

  const deleteRow = useCallback((idx) => {
    setActivity((prev) => prev.filter((_, i) => i !== idx))
  }, [])

  const clearAll = useCallback(() => {
    setActivity([])
    setSuite(null)
    setLive(null)
    clearHistory()
    notify('History deleted from this computer.', 'ok')
  }, [notify])

  const [title, desc] = TITLES[route] || TITLES['#overview']

  return (
    <div className="shell">
      <Sidebar route={route} health={health} />
      <div className="main">
        <Topbar title={title} desc={desc} health={health} onRetry={check} />
        <MobileNav route={route} />
        <div className="content">
          {route === '#overview' && <Overview activity={activity} suite={suite} live={live} phase={phase} onDeleteRow={deleteRow} onClearAll={clearAll} />}
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
