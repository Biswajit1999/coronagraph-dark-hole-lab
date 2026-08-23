export type Parameter = {
  key: string
  label: string
  unit: string
  min: number
  max: number
  step: number
  value: number
  description: string
}

export type Sample = { x: number; observed: number; model: number; reference?: number }
export type Metric = { label: string; value: string; detail: string; tone?: 'good' | 'warn' | 'neutral' }
export type StudyResult = { samples: Sample[]; metrics: Metric[]; conclusion: string; rows: string[][] }

export type Project = {
  shortName: string
  title: string
  eyebrow: string
  thesis: string
  description: string
  accent: string
  accent2: string
  xLabel: string
  yLabel: string
  observedLabel: string
  modelLabel: string
  parameters: Parameter[]
  assumptions: string[]
  methods: string[]
}
