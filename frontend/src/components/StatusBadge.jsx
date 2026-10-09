export function StatusBadge({ kind, children }) {
  return <span className={`badge ${kind || 'info'}`}>{children}</span>
}
