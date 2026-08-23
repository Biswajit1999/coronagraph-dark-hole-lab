import { useMemo, useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { Chart } from './Chart'
import { Controls } from './Controls'
import { project } from './project'
import { runModel } from './science'
import './styles.css'

const defaults = Object.fromEntries(project.parameters.map((parameter) => [parameter.key, parameter.value]))

function Icon({ name, size = 20 }: { name: 'atom' | 'book' | 'github' | 'sliders'; size?: number }) {
  const paths = {
    atom: <><circle cx="12" cy="12" r="1.8"/><ellipse cx="12" cy="12" rx="9" ry="3.7"/><ellipse cx="12" cy="12" rx="9" ry="3.7" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="9" ry="3.7" transform="rotate(120 12 12)"/></>,
    book: <><path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H11v17H7.5A3.5 3.5 0 0 0 4 22z"/><path d="M20 5.5A3.5 3.5 0 0 0 16.5 2H13v17h3.5A3.5 3.5 0 0 1 20 22z"/></>,
    github: <path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.87c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.35 1.09 2.92.83.09-.65.35-1.09.64-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.6 9.6 0 0 1 12 6.82a9.6 9.6 0 0 1 2.5.34c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.86v2.76c0 .27.18.58.69.48A10 10 0 0 0 12 2z"/>,
    sliders: <><path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/></>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

export default function App() {
  const [values, setValues] = useState<Record<string, number>>(defaults)
  const reduceMotion = useReducedMotion()
  const result = useMemo(() => runModel(values), [values])
  const entrance = reduceMotion ? {} : { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 } }
  return <div className="app" style={{'--accent':project.accent,'--accent-2':project.accent2} as React.CSSProperties}>
    <a className="skip-link" href="#main">Skip to model</a>
    <header className="topbar"><a className="brand" href="#top" aria-label={`${project.shortName} home`}><Icon name="atom" size={22}/><span>{project.shortName}</span></a><nav aria-label="Project links"><a href="#method"><Icon name="book"/>Method</a><a href="https://github.com/Biswajit1999" target="_blank" rel="noreferrer"><Icon name="github"/>GitHub</a></nav></header>
    <main id="main">
      <motion.section className="hero" {...entrance} transition={{type:'spring',stiffness:120,damping:20}}>
        <div><span className="eyebrow">{project.eyebrow}</span><h1>{project.title}</h1><p className="thesis">{project.thesis}</p><p>{project.description}</p></div>
        <div className="hero-orbit" aria-hidden="true"><span/><span/><span/><Icon name="sliders" size={34}/></div>
      </motion.section>
      <section className="workspace" aria-label="Interactive research workspace">
        <Controls parameters={project.parameters} values={values} onChange={(key,value)=>setValues((current)=>({...current,[key]:value}))} onReset={()=>setValues(defaults)} />
        <motion.div className="results" layout transition={{type:'spring',stiffness:180,damping:24}}>
          <div className="metrics">{result.metrics.map((metric,index)=><motion.article className={`metric ${metric.tone ?? 'neutral'}`} key={metric.label} initial={reduceMotion?false:{opacity:0,scale:.96}} animate={{opacity:1,scale:1}} transition={{delay:reduceMotion?0:index*.04}}><span>{metric.label}</span><strong>{metric.value}</strong><p>{metric.detail}</p></motion.article>)}</div>
          <Chart samples={result.samples} xLabel={project.xLabel} yLabel={project.yLabel} observedLabel={project.observedLabel} modelLabel={project.modelLabel}/>
          <div className="conclusion" role="status" aria-live="polite"><span>Current interpretation</span><p>{result.conclusion}</p></div>
        </motion.div>
      </section>
      <section id="method" className="method-section"><div><span className="kicker">Research contract</span><h2>What this model claims—and what it does not</h2><p>The workbench is an inspectable forward model for hypothesis formation and sensitivity analysis. It is not a substitute for instrument-specific calibration, Bayesian inference, or peer-reviewed validation.</p></div><div className="method-grid"><article><h3>Model chain</h3><ol>{project.methods.map((item)=><li key={item}>{item}</li>)}</ol></article><article><h3>Declared assumptions</h3><ul>{project.assumptions.map((item)=><li key={item}>{item}</li>)}</ul></article></div></section>
    </main>
    <footer><span>Built by Biswajit Jana · Astrophysics & instrumentation</span><span>MIT · Reproducible browser model</span></footer>
  </div>
}
