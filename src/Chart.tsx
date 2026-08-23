import type { Sample } from './types'

const W = 820
const H = 340
const PAD = 46

function pathFor(samples: Sample[], key: 'observed' | 'model', yMin: number, yMax: number) {
  const spanX = Math.max(samples.at(-1)?.x ?? 1, 1)
  const spanY = Math.max(yMax - yMin, Number.EPSILON)
  return samples.map((sample, index) => {
    const x = PAD + (sample.x / spanX) * (W - PAD * 2)
    const y = H - PAD - ((sample[key] - yMin) / spanY) * (H - PAD * 2)
    return `${index ? 'L' : 'M'} ${x.toFixed(2)} ${y.toFixed(2)}`
  }).join(' ')
}

export function Chart({ samples, xLabel, yLabel, observedLabel, modelLabel }: {
  samples: Sample[]; xLabel: string; yLabel: string; observedLabel: string; modelLabel: string
}) {
  const values = samples.flatMap((d) => [d.observed, d.model])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const margin = Math.max((max - min) * 0.12, 0.01)
  const yMin = min - margin
  const yMax = max + margin
  const ticks = Array.from({ length: 5 }, (_, i) => yMin + (i / 4) * (yMax - yMin))
  return (
    <figure className="chart-card" aria-labelledby="chart-title">
      <div className="chart-heading">
        <div><span className="kicker">Live diagnostic</span><h2 id="chart-title">Model response</h2></div>
        <div className="legend" aria-label="Chart legend"><span className="observed-dot" />{observedLabel}<span className="model-dot" />{modelLabel}</div>
      </div>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${observedLabel} and ${modelLabel} plotted against ${xLabel}`}>
        <defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--accent)" stopOpacity=".22"/><stop offset="1" stopColor="var(--accent)" stopOpacity="0"/></linearGradient></defs>
        {ticks.map((tick) => {
          const y = H - PAD - ((tick - yMin) / (yMax - yMin)) * (H - PAD * 2)
          return <g key={tick}><line x1={PAD} x2={W-PAD} y1={y} y2={y} className="gridline"/><text x={PAD-8} y={y+4} textAnchor="end" className="tick">{tick.toPrecision(3)}</text></g>
        })}
        <line x1={PAD} x2={W-PAD} y1={H-PAD} y2={H-PAD} className="axis"/>
        <path d={`${pathFor(samples,'model',yMin,yMax)} L ${W-PAD} ${H-PAD} L ${PAD} ${H-PAD} Z`} fill="url(#area)" />
        <path d={pathFor(samples,'observed',yMin,yMax)} className="observed-line" />
        <path d={pathFor(samples,'model',yMin,yMax)} className="model-line" />
        <text x={W/2} y={H-8} textAnchor="middle" className="axis-label">{xLabel}</text>
        <text x="14" y={H/2} textAnchor="middle" transform={`rotate(-90 14 ${H/2})`} className="axis-label">{yLabel}</text>
      </svg>
      <details className="data-table"><summary>Open accessible data table</summary><div className="table-scroll"><table><thead><tr><th>{xLabel}</th><th>{observedLabel}</th><th>{modelLabel}</th></tr></thead><tbody>{samples.filter((_,i)=>i%Math.max(1,Math.floor(samples.length/12))===0).map((d)=><tr key={d.x}><td>{d.x.toPrecision(4)}</td><td>{d.observed.toPrecision(5)}</td><td>{d.model.toPrecision(5)}</td></tr>)}</tbody></table></div></details>
    </figure>
  )
}
