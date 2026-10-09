import { I } from './icons'

export function MetricCard({ icon, label, value, sub, tone }) {
  return (
    <div className={`metric ${tone || ''}`}>
      <div className="lbl">{icon}<span>{label}</span></div>
      <div className="val">{value}</div>
      <div className="sub">{sub}</div>
    </div>
  )
}
export { I }
