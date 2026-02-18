import { useState, useEffect, useRef } from 'react'

const DEFAULT_ITEMS = [
  { id: '1', type: 'cycle',  prefix: '[CYCLE]',  text: 'Cycle 6 complete — accuracy 88%',              time: '12 min ago' },
  { id: '2', type: 'signal', prefix: '[SIGNAL]', text: 'Weather: 12.7°C London · flu season active',    time: '12 min ago' },
  { id: '3', type: 'nego',   prefix: '[NEGO]',   text: 'Negotiating with 3 vendors for SKU-001 Milk',   time: '11 min ago' },
  { id: '4', type: 'order',  prefix: '[ORDER]',  text: 'PO placed: 1540 × Milk → FreshFarm Dairy 6d',  time: '10 min ago' },
  { id: '5', type: 'order',  prefix: '[ORDER]',  text: 'PO placed: 470 × Paracetamol → NationalDist',  time: '10 min ago' },
  { id: '6', type: 'eval',   prefix: '[EVAL]',   text: 'Braintrust: lead time accuracy score 0.88',     time: '9 min ago' },
]

const TYPE_COLORS = {
  cycle:  'text-[#a78bfa]',
  signal: 'text-[#22d3ee]',
  nego:   'text-[#f4bf4f]',
  order:  'text-[#41d6ad]',
  eval:   'text-[#f4bf4f]',
  live:   'text-[#ff7a66]',
}

function ActivityRow({ item, isNew }) {
  const color = TYPE_COLORS[item.type] || 'text-slate-400'
  return (
    <div className={`flex items-start gap-2 py-1.5 border-b border-white/4 last:border-0 ${isNew ? 'animate-slide-in-right' : ''}`}>
      <span className={`font-mono text-[10px] font-semibold shrink-0 mt-px ${color}`}>
        {item.prefix || '[INFO]'}
      </span>
      <span className="terminal text-slate-300 flex-1 min-w-0 break-words">{item.text}</span>
      <span className="terminal text-slate-600 shrink-0 ml-2 whitespace-nowrap">{item.time}</span>
    </div>
  )
}

export default function ActivityFeed({ activities = [], liveStatus, liveStep, onViewAll }) {
  const [items, setItems] = useState(DEFAULT_ITEMS)
  const [newIds, setNewIds] = useState(new Set())

  useEffect(() => {
    if (!activities.length) return
    const mapped = activities.map(a => ({
      id: a.id,
      type: 'order',
      prefix: '[ORDER]',
      text: `${a.text}${a.meta ? ' — ' + a.meta : ''}`,
      time: a.time || 'Just now',
    }))
    setItems(mapped)
    const ids = new Set(mapped.slice(0, 3).map(m => m.id))
    setNewIds(ids)
    setTimeout(() => setNewIds(new Set()), 1000)
  }, [activities])

  return (
    <div className="glass-card p-5 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
          <span className="w-1 h-4 rounded-full bg-[#22d3ee] inline-block" />
          Agent Activity
        </h2>
        {onViewAll && (
          <button onClick={onViewAll} className="text-[10px] text-[#41d6ad] hover:text-[#41d6ad]/80 font-mono transition-colors">
            VIEW ALL →
          </button>
        )}
      </div>

      {liveStatus === 'running' && liveStep && (
        <div className="mb-3 p-2 rounded-lg bg-[#ff7a66]/8 border border-[#ff7a66]/20">
          <p className="terminal text-[#ff7a66] flex items-center gap-2">
            <span className="animate-pulse">●</span>
            <span>{liveStep}</span>
            <span className="cursor-blink">_</span>
          </p>
        </div>
      )}

      <div className="flex-1 overflow-y-auto min-h-0">
        {items.map(item => (
          <ActivityRow key={item.id} item={item} isNew={newIds.has(item.id)} />
        ))}
      </div>
    </div>
  )
}
