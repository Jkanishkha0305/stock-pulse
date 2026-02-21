const PRODUCTS_DEFAULT = [
  { sku: 'SKU-001', name: 'Fresh Whole Milk',     stock: 320,  reorderPoint: 400, daysLeft: 1,  velocity: 197 },
  { sku: 'SKU-002', name: 'Heinz Baked Beans',    stock: 890,  reorderPoint: 200, daysLeft: 11, velocity: 78  },
  { sku: 'SKU-003', name: 'Paracetamol 500mg',    stock: 85,   reorderPoint: 150, daysLeft: 2,  velocity: 29  },
  { sku: 'SKU-004', name: 'Pumpkin Soup',          stock: 45,   reorderPoint: 100, daysLeft: 3,  velocity: 11  },
  { sku: 'SKU-005', name: 'Energy Drinks 250ml',   stock: 180,  reorderPoint: 250, daysLeft: 2,  velocity: 62  },
]

const SKU_ICONS = {
  'SKU-001': '🥛',
  'SKU-002': '🥫',
  'SKU-003': '💊',
  'SKU-004': '🎃',
  'SKU-005': '⚡',
}

function statusConfig(days) {
  if (days <= 2)  return { color: '#ff7a66', ring: 'rgba(255,122,102,0.3)', label: 'CRITICAL', badge: 'bg-[#ff7a66]/15 text-[#ff7a66] border-[#ff7a66]/30' }
  if (days <= 7)  return { color: '#f4bf4f', ring: 'rgba(244,191,79,0.25)', label: 'LOW',      badge: 'bg-[#f4bf4f]/15 text-[#f4bf4f] border-[#f4bf4f]/30' }
  return              { color: '#41d6ad', ring: 'rgba(65,214,173,0.2)',  label: 'OK',       badge: 'bg-[#41d6ad]/15 text-[#41d6ad] border-[#41d6ad]/30' }
}

function DonutGauge({ pct, color, days }) {
  const r = 36
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - Math.min(pct, 1))
  return (
    <div className="relative flex items-center justify-center" style={{ width: 96, height: 96 }}>
      <svg width="96" height="96" viewBox="0 0 96 96" className="-rotate-90">
        {/* Track */}
        <circle cx="48" cy="48" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        {/* Fill */}
        <circle
          cx="48" cy="48" r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          className="donut-ring"
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold font-display tabular-nums" style={{ color }}>
          {days}
        </span>
        <span className="text-[9px] text-slate-500 leading-none">days</span>
      </div>
    </div>
  )
}

function SKUCard({ product }) {
  const days = product.daysLeft ?? 7
  const status = statusConfig(days)
  const maxStock = Math.max(product.stock, product.reorderPoint, 500)
  const stockPct = product.stock / maxStock
  const icon = SKU_ICONS[product.sku] || '📦'
  const isCritical = days <= 2

  return (
    <div
      className="glass-card flex flex-col gap-4 p-5 relative overflow-hidden transition-all hover:scale-[1.02]"
      style={{
        borderColor: status.color + '33',
        boxShadow: isCritical
          ? `0 0 0 1px ${status.color}22, 0 0 20px ${status.color}18`
          : `0 0 0 1px ${status.color}15`,
      }}
    >
      {/* Glow pulse for critical items */}
      {isCritical && (
        <div className="absolute inset-0 rounded-2xl pointer-events-none"
          style={{ boxShadow: `inset 0 0 30px ${status.color}15`, animation: 'glow-red 1.5s ease-in-out infinite' }}
        />
      )}

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 font-mono">{product.sku}</p>
          <p className="text-sm font-semibold text-slate-200 mt-0.5 leading-snug">{product.name}</p>
        </div>
        <span className="text-2xl">{icon}</span>
      </div>

      {/* Donut + stats */}
      <div className="flex items-center gap-4">
        <DonutGauge pct={stockPct} color={status.color} days={days} />
        <div className="flex flex-col gap-2 flex-1 min-w-0">
          <div>
            <p className="text-xs text-slate-500">Stock</p>
            <p className="text-base font-bold text-slate-200 tabular-nums">{product.stock.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Reorder at</p>
            <p className="text-sm text-slate-400 tabular-nums">{product.reorderPoint.toLocaleString()}</p>
          </div>
          {product.velocity != null && (
            <div>
              <p className="text-xs text-slate-500">Velocity</p>
              <p className="text-sm tabular-nums" style={{ color: status.color }}>{product.velocity}/day</p>
            </div>
          )}
        </div>
      </div>

      {/* Status badge */}
      <div className="flex items-center justify-between">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-mono font-semibold ${status.badge}`}>
          {isCritical && <span className="animate-ping-slow inline-block w-1.5 h-1.5 rounded-full" style={{ backgroundColor: status.color }} />}
          {status.label}
        </span>
        <span className="text-[10px] text-slate-500 font-mono">
          {days <= 7 ? `⚠ ${days}d left` : `✓ ${days}d left`}
        </span>
      </div>
    </div>
  )
}

export default function SKUCards({ products = [] }) {
  const list = products.length ? products : PRODUCTS_DEFAULT
  return (
    <div>
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
        <span className="w-1 h-4 rounded-full bg-[#41d6ad] inline-block" />
        Live Inventory
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {list.map(p => <SKUCard key={p.sku || p.id} product={p} />)}
      </div>
    </div>
  )
}
