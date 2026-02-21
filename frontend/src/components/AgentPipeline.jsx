const STEPS = [
  { id: 1, icon: '🗄️',  label: 'Fetch\nInventory',    desc: 'Pull stock levels from Supabase' },
  { id: 2, icon: '📊',  label: 'Demand\nForecast',     desc: 'Calculate days remaining + velocity' },
  { id: 3, icon: '🌤️',  label: 'Enrich\nSignals',      desc: 'Weather, festivals, season, trends' },
  { id: 4, icon: '🤖',  label: 'AI\nReasoning',        desc: 'Airia pipeline — decide reorder qty' },
  { id: 5, icon: '💬',  label: 'Vendor\nNegotiation',  desc: 'Chat with 3 vendors simultaneously' },
  { id: 6, icon: '🏆',  label: 'Pick\nBest Offer',     desc: 'Score by price × lead time × reliability' },
  { id: 7, icon: '✅',  label: 'Place PO\n& Log',       desc: 'Insert to Supabase, log reasoning' },
]

export default function AgentPipeline({ isRunning = false, currentStep = 0 }) {
  return (
    <div className="glass-card p-6">
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
        <span className="w-1 h-4 rounded-full bg-[#a78bfa] inline-block" />
        Agent Pipeline
        {isRunning && (
          <span className="ml-2 text-[10px] text-[#ff7a66] font-mono animate-pulse">● LIVE</span>
        )}
      </h2>

      <div className="flex items-start gap-0 overflow-x-auto pb-2">
        {STEPS.map((step, i) => {
          const isDone    = isRunning && currentStep > step.id
          const isActive  = isRunning && currentStep === step.id
          const isIdle    = !isRunning
          const isLast    = i === STEPS.length - 1

          return (
            <div key={step.id} className="flex items-center flex-shrink-0">
              {/* Step node */}
              <div className="flex flex-col items-center gap-2" style={{ minWidth: 80 }}>
                {/* Circle */}
                <div className="relative">
                  {isActive && (
                    <span className="absolute inset-0 rounded-full animate-ping-slow"
                      style={{ backgroundColor: 'rgba(167,139,250,0.3)' }}
                    />
                  )}
                  <div
                    className="relative w-11 h-11 rounded-full flex items-center justify-center text-lg transition-all duration-500"
                    style={{
                      background: isDone   ? 'rgba(65,214,173,0.2)'
                                : isActive ? 'rgba(167,139,250,0.25)'
                                : 'rgba(255,255,255,0.05)',
                      border: `2px solid ${isDone ? '#41d6ad' : isActive ? '#a78bfa' : 'rgba(255,255,255,0.1)'}`,
                      boxShadow: isActive ? '0 0 16px rgba(167,139,250,0.5)' : isDone ? '0 0 8px rgba(65,214,173,0.3)' : 'none',
                    }}
                  >
                    {isDone ? '✓' : step.icon}
                  </div>
                </div>

                {/* Label */}
                <p className="text-center text-[10px] leading-tight whitespace-pre-line font-medium"
                  style={{ color: isDone ? '#41d6ad' : isActive ? '#a78bfa' : '#64748b' }}>
                  {step.label}
                </p>

                {/* Active step description */}
                {isActive && (
                  <p className="text-[9px] text-[#a78bfa]/70 text-center max-w-[72px] leading-tight">
                    {step.desc}
                  </p>
                )}
              </div>

              {/* Connector */}
              {!isLast && (
                <div className="flex items-center" style={{ width: 24, marginTop: -28 }}>
                  <svg width="24" height="2" viewBox="0 0 24 2">
                    <line
                      x1="0" y1="1" x2="24" y2="1"
                      stroke={isDone ? '#41d6ad' : isActive ? '#a78bfa' : 'rgba(255,255,255,0.1)'}
                      strokeWidth="1.5"
                      className={isActive ? 'pipeline-flow' : ''}
                    />
                  </svg>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Idle state hint */}
      {!isRunning && (
        <p className="text-xs text-slate-600 mt-4 font-mono">
          ● Agent runs autonomously every hour — pipeline activates automatically
        </p>
      )}
    </div>
  )
}
