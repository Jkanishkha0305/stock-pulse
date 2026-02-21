import { useEffect, useRef, useState } from 'react'

function useCountUp(target, duration = 1400) {
  const [value, setValue] = useState(0)
  const prev = useRef(0)
  useEffect(() => {
    const start = prev.current
    const diff = target - start
    if (diff === 0) return
    const startTime = performance.now()
    const frame = (now) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out-cubic
      setValue(Math.round(start + diff * eased))
      if (progress < 1) requestAnimationFrame(frame)
      else prev.current = target
    }
    requestAnimationFrame(frame)
  }, [target, duration])
  return value
}

function KPICard({ label, sublabel, value, formatted, delta, color, icon }) {
  const colors = {
    mint:   { card: 'glass-card-glow-mint',   text: 'text-[#41d6ad]', glow: 'text-glow-mint',  delta: 'text-[#41d6ad]/80' },
    amber:  { card: 'glass-card-glow-amber',  text: 'text-[#f4bf4f]', glow: 'text-glow-amber', delta: 'text-[#f4bf4f]/80' },
    coral:  { card: 'glass-card-glow-coral',  text: 'text-[#ff7a66]', glow: 'text-glow-coral', delta: 'text-[#ff7a66]/80' },
    cyan:   { card: 'glass-card-glow-cyan',   text: 'text-[#22d3ee]', glow: 'text-glow-cyan',  delta: 'text-[#22d3ee]/80' },
    purple: { card: 'glass-card-glow-purple', text: 'text-[#a78bfa]', glow: '',                delta: 'text-[#a78bfa]/80' },
  }
  const c = colors[color] || colors.mint

  return (
    <div className={`${c.card} p-5 flex flex-col gap-3`}>
      <div className="flex items-start justify-between">
        <p className="text-slate-400 text-sm font-medium">{label}</p>
        <span className="text-xl">{icon}</span>
      </div>

      <div>
        <div className={`text-4xl font-bold font-display ${c.text} ${c.glow} tabular-nums`}>
          {formatted}
        </div>
        {delta && (
          <p className={`text-xs mt-1 ${c.delta}`}>{delta}</p>
        )}
        {sublabel && (
          <p className="text-slate-500 text-xs mt-0.5">{sublabel}</p>
        )}
      </div>
    </div>
  )
}

export default function KPICards({ accuracy = 88, accuracyDelta = 33, valueSaved = 12450, stockoutsAvoided = 6, cycleIndex = 6 }) {
  const animAccuracy     = useCountUp(accuracy, 1200)
  const animValue        = useCountUp(valueSaved, 1500)
  const animStockouts    = useCountUp(stockoutsAvoided, 1000)
  const animCycle        = useCountUp(cycleIndex, 800)

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <KPICard
        label="Prediction Accuracy"
        delta={`↑ +${accuracyDelta}% since Cycle 1`}
        value={accuracy}
        formatted={`${animAccuracy}%`}
        color="mint"
        icon="🎯"
      />
      <KPICard
        label="Value Saved"
        sublabel="in lost sales prevented"
        value={valueSaved}
        formatted={`£${animValue.toLocaleString()}`}
        color="amber"
        icon="💰"
      />
      <KPICard
        label="Stockouts Avoided"
        sublabel="this month"
        value={stockoutsAvoided}
        formatted={String(animStockouts)}
        color="coral"
        icon="🛡️"
      />
      <KPICard
        label="Learning Cycle"
        sublabel="autonomous cycles run"
        value={cycleIndex}
        formatted={`#${animCycle}`}
        color="purple"
        icon="🔄"
      />
    </div>
  )
}
