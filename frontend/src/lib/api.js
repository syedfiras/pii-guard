const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function req(path, opts) {
  const r = await fetch(`${API}${path}`, opts)
  if (!r.ok) throw new Error(`HTTP ${r.status} on ${path}`)
  return r.json()
}

export const apiBase = API
export const getHealth = () => req('/api/health')
export const getLogs = () => req('/api/tool-logs')
export function invoke(payload, types, aadhaarStrict) {
  return req('/api/invoke', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool: 'send_sms', payload, types, aadhaar_strict: aadhaarStrict }),
  })
}
export function agentChat(message, guard) {
  return req('/api/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, guard }),
  })
}

export function toText(payload) {
  if (typeof payload === 'string') return payload
  if (payload && typeof payload === 'object' && typeof payload.text === 'string' && Object.keys(payload).length === 1)
    return payload.text
  try { return JSON.stringify(payload, null, 2) } catch { return String(payload) }
}

/** Count fake tokens in a sanitized payload string (vault formats). */
export function countTokens(s) {
  if (!s) return 0
  const pats = [/user_\d+__@redacted\.test/g, /\+91-00000-\d+/g, /QWERT\d+Z/g, /2999-8888-\d+/g, /(?:4111|5555|6011)(?: \d{4}){3}|3782 \d{6} \d{5}/g]
  let n = 0
  pats.forEach((p) => { n += (s.match(p) || []).length })
  return n
}
