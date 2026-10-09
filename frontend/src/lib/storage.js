/* History that survives refresh. Only counts and statuses are stored here —
   never real messages or personal details. The chat box stays memory-only
   on purpose, so typed personal details vanish on refresh. */
const KEY = 'veil-guard-history-v1'
const MAX_ROWS = 30

export function loadHistory() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return { activity: [], suite: null }
    const d = JSON.parse(raw)
    return {
      activity: Array.isArray(d.activity) ? d.activity.slice(-MAX_ROWS) : [],
      suite: d.suite || null,
    }
  } catch {
    return { activity: [], suite: null }
  }
}

export function saveHistory(activity, suite) {
  try {
    localStorage.setItem(KEY, JSON.stringify({
      activity: (activity || []).slice(-MAX_ROWS),
      suite: suite || null,
    }))
  } catch {
    /* storage full or blocked — app keeps working without it */
  }
}

export function clearHistory() {
  try { localStorage.removeItem(KEY) } catch { /* noop */ }
}
