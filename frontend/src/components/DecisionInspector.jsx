function urgencyTone(daysLeft) {
  if (daysLeft <= 3) return 'Critical'
  if (daysLeft <= 7) return 'Watch'
  return 'Stable'
}

function urgencyClasses(tone) {
  if (tone === 'Critical') return 'text-red-300 border-red-500/40 bg-red-500/10'
  if (tone === 'Watch') return 'text-amber-300 border-amber-500/40 bg-amber-500/10'
  return 'text-emerald-300 border-emerald-500/40 bg-emerald-500/10'
}

export default function DecisionInspector({ product, cycleIndex = 6 }) {
  if (!product) {
    return (
      <section className="surface-card p-5">
        <h2 className="font-display text-lg text-slate-100">Decision Inspector</h2>
        <p className="mt-2 text-sm text-slate-400">
          Select an SKU in Inventory Radar to inspect the agent recommendation.
        </p>
      </section>
    )
  }

  const daysLeft = product.daysLeft ?? 0
  const stock = Number(product.stock ?? 0)
  const reorderPoint = Number(product.reorderPoint ?? 0)
  const estimatedVelocity = daysLeft > 0 ? Math.max(1, stock / daysLeft) : Math.max(1, stock / 7)
  const leadDays = 7
  const safetyBufferDays = 3
  const deficit = Math.max(0, reorderPoint - stock)
  const suggestedQty = Math.max(
    0,
    Math.round((leadDays + safetyBufferDays) * estimatedVelocity + deficit),
  )

  const tone = urgencyTone(daysLeft)

  return (
    <section className="surface-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="label-caps">Decision Inspector</p>
          <h2 className="font-display mt-1 text-xl text-slate-100">
            {product.sku ?? product.id} · {product.name}
          </h2>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] ${urgencyClasses(
            tone,
          )}`}
        >
          {tone}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="metric-tile p-3">
          <p className="text-xs text-slate-400">Days Remaining</p>
          <p className="mt-1 text-2xl font-semibold text-slate-100">{Math.max(0, daysLeft)}</p>
        </div>
        <div className="metric-tile p-3">
          <p className="text-xs text-slate-400">Suggested Order</p>
          <p className="mt-1 text-2xl font-semibold text-emerald-300">{suggestedQty} units</p>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-slate-700/80 bg-slate-950/45 p-4">
        <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Reasoning Formula</p>
        <p className="mt-2 text-sm text-slate-300">
          ({leadDays} lead + {safetyBufferDays} buffer) × {estimatedVelocity.toFixed(1)} velocity + {deficit} deficit
        </p>
        <p className="mt-2 text-xs text-slate-400">
          Cycle {cycleIndex}: prioritizing this SKU to avoid stockout before supplier arrival.
        </p>
      </div>
    </section>
  )
}
