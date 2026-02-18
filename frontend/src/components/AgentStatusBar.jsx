import { useState, useEffect } from 'react'

const CYCLE_INTERVAL_SECS = 3600 // 1 hour

export default function AgentStatusBar({ cycleIndex, isRunning, onForceRun, liveStep }) {
  const [clock, setClock] = useState('')
  const [secondsUntilNext, setSecondsUntilNext] = useState(CYCLE_INTERVAL_SECS)

  // Live clock
  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString('en-GB', { hour12: false }))
    tick()
    const t = setInterval(tick, 1000)
    return () => clearInterval(t)
  }, [])

  // Countdown to next auto-cycle
  useEffect(() => {
    if (isRunning) { setSecondsUntilNext(CYCLE_INTERVAL_SECS); return }
    const t = setInterval(() => {
      setSecondsUntilNext(s => {
        if (s <= 1) return CYCLE_INTERVAL_SECS
        return s - 1
      })
    }, 1000)
    return () => clearInterval(t)
  }, [isRunning])

  const mm = String(Math.floor(secondsUntilNext / 60)).padStart(2, '0')
  const ss = String(secondsUntilNext % 60).padStart(2, '0')

  return (
    <div className="glass-card border-white/10 px-5 py-3 flex flex-wrap items-center justify-between gap-3 text-sm">
      {/* Left: live indicator + step */}
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${isRunning ? 'animate-ping bg-[#ff7a66]' : 'animate-ping-slow bg-[#41d6ad]'}`} />
            <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${isRunning ? 'bg-[#ff7a66]' : 'bg-[#41d6ad]'}`} />
          </span>
          <span className={`font-mono font-semibold text-xs tracking-widest ${isRunning ? 'text-[#ff7a66]' : 'text-[#41d6ad]'}`}>
            {isRunning ? 'RUNNING' : 'ACTIVE'}
          </span>
        </span>

        {isRunning && liveStep && (
          <span className="terminal text-slate-400 animate-pulse">{liveStep}</span>
        )}
        {!isRunning && (
          <span className="text-slate-400 text-xs">
            Next cycle in <span className="font-mono text-slate-300">{mm}:{ss}</span>
          </span>
        )}
      </div>

      {/* Right: status chips + clock + force run */}
      <div className="flex items-center gap-3 flex-wrap">
        <Chip label="AI" value="ACTIVE" color="mint" />
        <Chip label="DB" value="CONNECTED" color="cyan" />
        <Chip label="EVAL" value="RUNNING" color="purple" />

        <span className="font-mono text-slate-400 text-xs tabular-nums ml-1">{clock}</span>

        <button
          onClick={onForceRun}
          disabled={isRunning}
          className="ml-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
            border-[#41d6ad]/30 text-[#41d6ad] hover:bg-[#41d6ad]/10
            disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Force Cycle
        </button>
      </div>
    </div>
  )
}

function Chip({ label, value, color }) {
  const colors = {
    mint:   'bg-[#41d6ad]/10 text-[#41d6ad] border-[#41d6ad]/20',
    cyan:   'bg-[#22d3ee]/10 text-[#22d3ee] border-[#22d3ee]/20',
    purple: 'bg-[#a78bfa]/10 text-[#a78bfa] border-[#a78bfa]/20',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-mono font-medium ${colors[color]}`}>
      <span className="text-slate-500">{label}:</span> {value}
    </span>
  )
}
