import { useState } from 'react'
import { I } from './icons'
import { highlight } from '../lib/highlight'

export function ComparisonPanel({ title, sub, tone, body, values, markCls, empty }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try { await navigator.clipboard.writeText(body || ''); setCopied(true); setTimeout(() => setCopied(false), 1200) }
    catch { /* clipboard unavailable */ }
  }
  return (
    <div className="panel">
      <header>
        <span>{title}</span><small>{sub}</small>
        <span className="sp">
          <button className="iconbtn" onClick={copy} aria-label={`Copy ${title}`}>
            {I.copy({ width: 13, height: 13 })} {copied ? 'copied' : 'copy'}
          </button>
        </span>
      </header>
      <div className="body" style={tone ? { borderTop: `2px solid ${tone}` } : undefined}>
        {body ? highlight(body, values, markCls) : <span style={{ color: 'var(--muted)' }}>{empty}</span>}
      </div>
    </div>
  )
}
