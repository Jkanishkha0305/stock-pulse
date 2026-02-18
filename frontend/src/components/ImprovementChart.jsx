import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Label,
} from 'recharts'

const DEFAULT_DATA = [
  { cycle: 'C1', accuracy: 55, label: 'Wrong lead times' },
  { cycle: 'C2', accuracy: 58, label: 'Early correction' },
  { cycle: 'C3', accuracy: 63, label: 'Flu season detected' },
  { cycle: 'C4', accuracy: 71, label: 'Seasonal patterns learned' },
  { cycle: 'C5', accuracy: 82, label: 'Pre-ordering 3wk early' },
  { cycle: 'C6', accuracy: 88, label: 'Optimised predictions' },
]

const CustomDot = ({ cx, cy }) => (
  <circle cx={cx} cy={cy} r={5} fill="#41d6ad" stroke="#070d1a" strokeWidth={2}
    style={{ filter: 'drop-shadow(0 0 4px #41d6ad)' }}
  />
)

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const data = payload[0]?.payload
  return (
    <div className="glass-card p-3 text-xs border-[#41d6ad]/20">
      <p className="text-slate-400 font-mono mb-1">{label}</p>
      <p className="text-[#41d6ad] font-bold text-lg">{payload[0]?.value}%</p>
      {data?.label && <p className="text-slate-500 mt-1">{data.label}</p>}
    </div>
  )
}

export default function ImprovementChart({ data = [] }) {
  const chartData = data.length ? data : DEFAULT_DATA

  return (
    <div className="glass-card p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
            <span className="w-1 h-4 rounded-full bg-[#41d6ad] inline-block" />
            Agent Learning Curve
          </h2>
          <p className="text-slate-500 text-xs mt-1">Prediction accuracy improving each autonomous cycle</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-[#41d6ad] text-glow-mint font-display tabular-nums">88%</p>
          <p className="text-xs text-slate-500">current accuracy</p>
        </div>
      </div>

      <div className="h-52">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id="accuracyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#41d6ad" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#41d6ad" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="cycle" stroke="#1e293b"
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
            <YAxis domain={[40, 100]} stroke="#1e293b"
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              tickFormatter={v => `${v}%`} />
            <ReferenceLine y={61} stroke="rgba(244,191,79,0.35)" strokeDasharray="5 4">
              <Label value="Human baseline 61%" position="insideTopRight"
                fill="rgba(244,191,79,0.55)" fontSize={10} fontFamily="JetBrains Mono" />
            </ReferenceLine>
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="accuracy"
              stroke="#41d6ad" strokeWidth={2.5}
              fill="url(#accuracyGrad)"
              dot={<CustomDot />}
              activeDot={{ r: 7, fill: '#41d6ad', stroke: '#070d1a', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex gap-6 mt-4 flex-wrap">
        <p className="text-xs text-slate-500">
          <span className="text-slate-400">C1:</span> 55% — agent using default lead times, no seasonal awareness
        </p>
        <p className="text-xs text-slate-500">
          <span className="text-[#41d6ad]">C6:</span> 88% — pre-orders 3 weeks early, zero stockouts
        </p>
      </div>
    </div>
  )
}
