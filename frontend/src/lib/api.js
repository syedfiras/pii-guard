const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function req(path, opts) {
  const r = await fetch(`${API}${path}`, opts)
  if (!r.ok) throw new Error(`HTTP ${r.status} on ${path}`)
  return r.json()
}

export const apiBase = API
export const getHealth = () => req('/api/health')
export const getLogs = () => req('/api/tool-logs')
export const getChain = () => req('/api/chain')
export const getPolicy = () => req('/api/policy')
export const reloadPolicy = () => req('/api/policy/reload', { method: 'POST' })
export const rotateKey = () => req('/api/vault/rotate', { method: 'POST' })
export function invoke(payload, types, aadhaarStrict, sessionId) {
  return req('/api/invoke', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool: 'send_sms', payload, types, aadhaar_strict: aadhaarStrict, session_id: sessionId || null }),
  })
}
export function agentChat(message, guard, sessionId) {
  return req('/api/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, guard, session_id: sessionId || null }),
  })
}
export function revealTokens(sessionId, tokens) {
  return req('/api/vault/reveal', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, tokens }),
  })
}
export function wipeVault(sessionId) {
  return req('/api/vault/wipe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId || null }),
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
  const pats = [/[a-z0-9-]+@redacted\.test/g, /\+91-0\d{4}-\d{5}/g, /QWERT\d{4}[A-Z]/g, /2999-8888-\d{4}/g, /(?:4111|5555|6011)(?: \d{4}){3}|3782 \d{6} \d{5}/g]
  let n = 0
  pats.forEach((p) => { n += (s.match(p) || []).length })
  return n
}
