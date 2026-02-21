function status(days) {
  if (days <= 3) return 'critical'
  if (days <= 7) return 'watch'
  return 'healthy'
}

function statusClasses(level) {
  if (level === 'critical') return 'text-red-200 border-red-500/35 bg-red-500/10'
  if (level === 'watch') return 'text-amber-200 border-amber-500/35 bg-amber-500/10'
  return 'text-emerald-200 border-emerald-500/35 bg-emerald-500/10'
}

function riskScore(product) {
  const days = product.daysLeft ?? 30
  const stock = Number(product.stock ?? 0)
  const reorder = Number(product.reorderPoint ?? 0)
  const deficitRatio = reorder > 0 ? Math.max(0, reorder - stock) / reorder : 0
  const dayPressure = Math.max(0, (14 - days) / 14)
  return Math.round(Math.min(99, (deficitRatio * 0.6 + dayPressure * 0.4) * 100))
}

export default function InventoryTable({
  products = [],
  selectedSku = null,
  onSelectSku,
}) {
  const defaultProducts = [
    { sku: 'SKU-001', name: 'Milk', stock: 420, reorderPoint: 300, daysLeft: 14 },
    { sku: 'SKU-002', name: 'Beans', stock: 240, reorderPoint: 200, daysLeft: 18 },
    { sku: 'SKU-003', name: 'Paracetamol', stock: 85, reorderPoint: 100, daysLeft: 7 },
    { sku: 'SKU-004', name: 'Pumpkin Soup', stock: 45, reorderPoint: 80, daysLeft: 3 },
    { sku: 'SKU-005', name: 'Energy Drinks', stock: 280, reorderPoint: 200, daysLeft: 11 },
  ]
  const list = products.length ? products : defaultProducts
  const criticalCount = list.filter((product) => (product.daysLeft ?? 99) <= 3).length
  const watchCount = list.filter((product) => (product.daysLeft ?? 99) > 3 && (product.daysLeft ?? 99) <= 7).length

  return (
    <section className="surface-card p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="label-caps">Detect</p>
          <h2 className="font-display mt-1 text-xl text-slate-100">Inventory Radar</h2>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="rounded-full border border-red-500/35 bg-red-500/10 px-3 py-1 text-red-200">
            {criticalCount} critical
          </span>
          <span className="rounded-full border border-amber-500/35 bg-amber-500/10 px-3 py-1 text-amber-200">
            {watchCount} watch
          </span>
        </div>
      </div>

      <div className="space-y-2">
        {list.map((p) => {
          const skuId = p.sku ?? p.id
          const days = p.daysLeft ?? 7
          const score = riskScore(p)
          const level = status(days)
          const selected = selectedSku === skuId

          return (
            <button
              type="button"
              key={skuId}
              onClick={() => onSelectSku?.(skuId)}
              className={`w-full rounded-xl border p-3 text-left transition ${
                selected
                  ? 'border-cyan-400/50 bg-cyan-500/10'
                  : 'border-slate-700/70 bg-slate-900/45 hover:border-slate-500/70 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-100">
                    {skuId} · {p.name}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Stock {p.stock} / Reorder {p.reorderPoint}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full border px-2.5 py-1 text-xs font-medium uppercase tracking-[0.12em] ${statusClasses(
                      level,
                    )}`}
                  >
                    {level}
                  </span>
                  <span className="rounded-full border border-slate-600/70 bg-slate-900/70 px-2.5 py-1 text-xs text-slate-300">
                    Risk {score}
                  </span>
                </div>
              </div>
              <div className="mt-3">
                <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      level === 'critical'
                        ? 'bg-red-400'
                        : level === 'watch'
                          ? 'bg-amber-400'
                          : 'bg-emerald-400'
                    }`}
                    style={{ width: `${Math.max(8, Math.min(100, 100 - score))}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  {days <= 3 ? `${days} days remaining: reorder immediately` : `${days} days remaining`}
                </p>
              </div>
            </button>
          )
        })}
      </div>
    </section>
  )
}
