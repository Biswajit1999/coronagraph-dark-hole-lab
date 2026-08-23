import type { Parameter } from './types'

export function Controls({ parameters, values, onChange, onReset }: {
  parameters: Parameter[]; values: Record<string, number>; onChange: (key: string, value: number) => void; onReset: () => void
}) {
  return <aside className="controls" aria-labelledby="controls-title">
    <div className="panel-heading"><div><span className="kicker">Experiment controls</span><h2 id="controls-title">Parameter space</h2></div><button className="quiet-button" onClick={onReset}>Reset</button></div>
    <div className="control-list">{parameters.map((parameter) => <div className="control" key={parameter.key}>
      <div className="control-label"><label htmlFor={parameter.key}>{parameter.label}</label><output htmlFor={parameter.key}>{values[parameter.key].toFixed(parameter.step < 0.1 ? 2 : parameter.step < 1 ? 1 : 0)} <span>{parameter.unit}</span></output></div>
      <input id={parameter.key} type="range" min={parameter.min} max={parameter.max} step={parameter.step} value={values[parameter.key]} onChange={(event)=>onChange(parameter.key,Number(event.target.value))} aria-describedby={`${parameter.key}-help`} />
      <p id={`${parameter.key}-help`}>{parameter.description}</p>
    </div>)}</div>
  </aside>
}
