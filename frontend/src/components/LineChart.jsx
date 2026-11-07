// Plain SVG line chart (no chart library).
//
// SVG coordinates start at (0,0) in the top-left and y grows downwards.
// So when converting a value to a y pixel we flip it (see the y() function).

const W = 640
const H = 230
const PAD = { left: 42, right: 14, top: 14, bottom: 28 }

export default function LineChart({ title, data, series, yMax, ticks, unit = '', guides = [], step = false }) {
  const innerW = W - PAD.left - PAD.right
  const innerH = H - PAD.top - PAD.bottom
  const n = data.length

  const x = (i) => PAD.left + (n <= 1 ? 0 : (i / (n - 1)) * innerW)
  const y = (v) => PAD.top + innerH - (Math.min(Math.max(v, 0), yMax) / yMax) * innerH

  // Build the path string: M = move to, L = line to, step=true draws staircase lines
  function buildPath(key) {
    return data
      .map((d, i) => {
        if (i === 0) return `M${x(i)},${y(d[key])}`
        if (step) return `L${x(i)},${y(data[i - 1][key])} L${x(i)},${y(d[key])}`
        return `L${x(i)},${y(d[key])}`
      })
      .join(' ')
  }

  return (
    <section className="card">
      <div className="card-head">
        <h2>{title}</h2>
        <div className="legend">
          {series.map((s) => (
            <span key={s.key}>
              <i style={{ background: s.color }} /> {s.label}
            </span>
          ))}
        </div>
      </div>

      {n < 2 ? (
        <p className="muted empty">Collecting data... waiting for at least 2 readings.</p>
      ) : (
        <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label={title}>
          {/* horizontal grid + y labels */}
          {ticks.map((t) => (
            <g key={t}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} className="grid-line" />
              <text x={PAD.left - 8} y={y(t) + 4} textAnchor="end" className="axis-text">
                {t}
                {unit}
              </text>
            </g>
          ))}

          {/* threshold guide lines */}
          {guides.map((g) => (
            <g key={g.label}>
              <line
                x1={PAD.left}
                x2={W - PAD.right}
                y1={y(g.value)}
                y2={y(g.value)}
                stroke={g.color}
                strokeDasharray="5 4"
                strokeWidth="1.5"
              />
              <text x={W - PAD.right - 4} y={y(g.value) - 4} textAnchor="end" className="axis-text" fill={g.color}>
                {g.label} ({g.value}
                {unit})
              </text>
            </g>
          ))}

          {/* data lines */}
          {series.map((s) => (
            <path key={s.key} d={buildPath(s.key)} fill="none" stroke={s.color} strokeWidth="2.2" strokeLinejoin="round" />
          ))}

          {/* x labels: first and last time */}
          <text x={PAD.left} y={H - 8} className="axis-text">
            {data[0].t}
          </text>
          <text x={W - PAD.right} y={H - 8} textAnchor="end" className="axis-text">
            {data[n - 1].t}
          </text>
        </svg>
      )}
    </section>
  )
}
