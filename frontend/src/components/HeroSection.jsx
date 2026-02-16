import { useState } from 'react'

const PIPELINE_STEPS = [
  'Detect risk',
  'Forecast demand',
  'Check suppliers',
  'Place orders',
]

export default function HeroSection({
  accuracy = 88,
  accuracyDelta = 33,
  valueSaved = 12450,
  stockoutsAvoided = 6,
  cycleIndex = 6,
  liveStep = null,
  onRunCycle,
  disabled,
}) {
  const [status, setStatus] = useState('idle') // idle | running | complete
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(0)

  const handleRun = async () => {
    if (status === 'running' || disabled) {
      return
    }
    setStatus('running')
    setProgress(0)
    setCurrentStep(0)

    let step = 0
    const interval = setInterval(() => {
      step += 1
      if (step >= PIPELINE_STEPS.length) {
        clearInterval(interval)
        return
      }
      setCurrentStep(step)
      setProgress(((step + 1) / PIPELINE_STEPS.length) * 100)
    }, 650)

    try {
      await onRunCycle?.()
    } catch (_) {
      // Keep motion complete for demo mode.
    } finally {
      clearInterval(interval)
    }

    setStatus('complete')
    setProgress(100)
    setCurrentStep(PIPELINE_STEPS.length - 1)
    setTimeout(() => setStatus('idle'), 2000)
  }

  const isRunning = status === 'running' || disabled
  const isComplete = status === 'complete'

  const metrics = [
    {
      label: 'Prediction Accuracy',
      value: `${accuracy}%`,
      accent: 'text-emerald-300',
      helper: `+${accuracyDelta}% vs cycle 1`,
    },
    {
      label: 'Value Protected',
      value: `£${valueSaved.toLocaleString()}`,
      accent: 'text-amber-300',
      helper: 'forecasted monthly impact',
    },
    {
      label: 'Stockouts Avoided',
      value: `${stockoutsAvoided}`,
      accent: 'text-cyan-300',
      helper: 'critical misses prevented',
    },
  ]

  return (
    <section className="surface-card animate-lift overflow-hidden p-5 sm:p-6">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="label-caps">Mission Overview</p>
          <h2 className="font-display mt-1 text-2xl text-slate-100">Cycle {cycleIndex} Command</h2>
          <p className="mt-2 text-sm text-slate-400">
            Run a full autonomous decision cycle and stream actions in real time.
          </p>
        </div>
        <button
          type="button"
          onClick={handleRun}
          disabled={disabled}
          className={`group rounded-2xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em] transition ${
            isRunning
              ? 'cursor-not-allowed bg-slate-800 text-slate-400'
              : 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 shadow-[0_12px_30px_rgba(40,193,157,0.35)] hover:translate-y-[-1px]'
          }`}
        >
          {isRunning ? 'Running cycle...' : isComplete ? 'Cycle complete' : 'Run Agent Cycle'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="metric-tile">
            <p className="text-xs text-slate-400">{metric.label}</p>
            <p className={`mt-1 text-2xl font-semibold ${metric.accent}`}>{metric.value}</p>
            <p className="mt-1 text-xs text-slate-500">{metric.helper}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-2xl border border-slate-700/80 bg-slate-950/40 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Pipeline</p>
          <p className="text-xs font-medium text-slate-300">{Math.round(progress)}%</p>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-500"
            style={{ width: `${Math.max(progress, isComplete ? 100 : 12)}%` }}
          />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {PIPELINE_STEPS.map((label, index) => {
            const state =
              index < currentStep || isComplete ? 'done' : index === currentStep ? 'active' : 'pending'
            return (
              <div
                key={label}
                className={`rounded-xl border px-3 py-2 text-xs ${
                  state === 'done'
                    ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                    : state === 'active'
                      ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-200'
                      : 'border-slate-700/70 bg-slate-900/50 text-slate-500'
                }`}
              >
                {label}
              </div>
            )
          })}
        </div>
        {(isRunning || liveStep) && (
          <p className="mt-3 text-sm text-slate-300">
            {liveStep ?? `Step ${currentStep + 1}: ${PIPELINE_STEPS[currentStep]}`}
          </p>
        )}
      </div>
    </section>
  )
}
