export function highlight(text, values, cls) {
  if (!values?.length || !text) return text
  const vals = [...new Set(values)].filter(Boolean).sort((a, b) => b.length - a.length)
  let parts = [text]
  vals.forEach((v) => {
    const next = []
    parts.forEach((p) => {
      if (typeof p !== 'string') { next.push(p); return }
      p.split(v).forEach((s, i, arr) => {
        next.push(s)
        if (i < arr.length - 1) next.push({ __m: v })
      })
    })
    parts = next
  })
  /* eslint-disable react/jsx-key */
  return parts.map((p, i) => typeof p === 'string'
    ? <span key={i}>{p}</span>
    : <mark key={i} className={cls}>{p.__m}</mark>)
}
