import { useState, useEffect, useCallback } from 'react'
import AgentStatusBar from './AgentStatusBar'
import KPICards from './KPICards'
import SKUCards from './SKUCards'
import AgentPipeline from './AgentPipeline'
import ActivityFeed from './ActivityFeed'
import ImprovementChart from './ImprovementChart'
import VendorNegotiationTab from './VendorNegotiationTab'
import { getDashboard, runCycle, getVendorNegotiation } from '../lib/api'

const PIPELINE_STEPS = [
  'Fetching inventory from Supabase...',
  'Calculating demand forecasts + velocity...',
  'Enriching with weather, festivals, season...',
  'Airia AI reasoning — deciding quantities...',
  'Negotiating with 3 vendors simultaneously...',
  'Scoring offers: price × lead time...',
  'Placing purchase orders + logging...',
]

const TABS = [
  { id: 'overview',     label: 'Overview',            icon: '📊' },
  { id: 'negotiation',  label: 'Vendor Negotiation',  icon: '💬' },
]

export default function Dashboard() {
  const [dashboard, setDashboard]     = useState(null)
  const [activities, setActivities]   = useState([])
  const [negotiations, setNegotiations] = useState(null)
  const [tab, setTab]                 = useState('overview')
  const [isRunning, setIsRunning]     = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [liveStep, setLiveStep]       = useState(null)
  const [error, setError]             = useState(null)

  const loadDashboard = useCallback(async () => {
    try {
      const data = await getDashboard()
      setDashboard(data)
      if (data?.activities) setActivities(data.activities)
      setError(null)
    } catch {
      setError('Backend not reachable — showing demo data')
    }
  }, [])

  useEffect(() => { loadDashboard() }, [loadDashboard])

  const handleForceRun = useCallback(async () => {
    if (isRunning) return
    setIsRunning(true)
    setCurrentStep(1)

    // Animate through pipeline steps
    let step = 1
    const interval = setInterval(() => {
      step += 1
      setCurrentStep(step)
      setLiveStep(PIPELINE_STEPS[step - 1] || PIPELINE_STEPS[PIPELINE_STEPS.length - 1])
      if (step >= PIPELINE_STEPS.length) clearInterval(interval)
    }, 900)

    try {
      await runCycle()
      // Load fresh negotiation data
      try {
        const neg = await getVendorNegotiation()
        setNegotiations(neg)
      } catch {}
      await loadDashboard()
    } catch {
      // demo mode: still animate
      await new Promise(r => setTimeout(r, 2000))
    } finally {
      clearInterval(interval)
      setIsRunning(false)
      setCurrentStep(0)
      setLiveStep(null)
    }
  }, [isRunning, loadDashboard])

  // Load negotiations on mount
  useEffect(() => {
    getVendorNegotiation().then(setNegotiations).catch(() => {})
  }, [])

  const d = dashboard ?? {}
  const products = d.products ?? []
  const cycleHistory = d.cycleHistory ?? []

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ────────────────────────────────────── */}
      <header className="px-6 py-4 flex items-center justify-between border-b border-white/6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#41d6ad]/15 border border-[#41d6ad]/30 flex items-center justify-center text-sm">
            📦
          </div>
          <div>
            <h1 className="font-display font-bold text-slate-100 text-lg leading-none">StockPulse</h1>
            <p className="text-[10px] text-slate-500 mt-0.5">AI Inventory Intelligence</p>
          </div>
        </div>
        <div className="text-xs text-slate-500 font-mono">
          Cycle {d.cycleIndex ?? 6} · Accuracy {d.accuracy ?? 88}%
        </div>
      </header>

      <div className="flex-1 px-4 md:px-6 py-4 space-y-4 max-w-[1400px] mx-auto w-full">
        {/* ── Error banner ──────────────────────────────── */}
        {error && (
          <div className="py-2 px-4 rounded-lg bg-[#f4bf4f]/8 border border-[#f4bf4f]/25 text-[#f4bf4f] text-xs terminal">
            ⚠ {error}
          </div>
        )}

        {/* ── Agent status bar ──────────────────────────── */}
        <AgentStatusBar
          cycleIndex={d.cycleIndex ?? 6}
          isRunning={isRunning}
          onForceRun={handleForceRun}
          liveStep={liveStep}
        />

        {/* ── KPI cards ─────────────────────────────────── */}
        <KPICards
          accuracy={d.accuracy ?? 88}
          accuracyDelta={d.accuracyDelta ?? 33}
          valueSaved={d.valueSaved ?? 12450}
          stockoutsAvoided={d.stockoutsAvoided ?? 6}
          cycleIndex={d.cycleIndex ?? 6}
        />

        {/* ── Tab nav ───────────────────────────────────── */}
        <div className="flex gap-1 p-1 rounded-xl bg-white/4 border border-white/6 w-fit">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                tab === t.id
                  ? 'bg-[#41d6ad]/15 text-[#41d6ad] border border-[#41d6ad]/25'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>{t.icon}</span> {t.label}
              {t.id === 'negotiation' && (
                <span className="text-[9px] font-mono bg-[#f4bf4f]/15 text-[#f4bf4f] px-1.5 py-0.5 rounded-full">NEW</span>
              )}
            </button>
          ))}
        </div>

        {/* ── Overview tab ──────────────────────────────── */}
        {tab === 'overview' && (
          <div className="space-y-4">
            {/* SKU cards */}
            <SKUCards products={products} />

            {/* Pipeline + Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
              <div className="lg:col-span-3">
                <AgentPipeline isRunning={isRunning} currentStep={currentStep} />
              </div>
              <div className="lg:col-span-2" style={{ minHeight: 280 }}>
                <ActivityFeed
                  activities={activities}
                  liveStatus={isRunning ? 'running' : null}
                  liveStep={liveStep}
                />
              </div>
            </div>

            {/* Learning chart */}
            <ImprovementChart data={cycleHistory} />
          </div>
        )}

        {/* ── Vendor Negotiation tab ────────────────────── */}
        {tab === 'negotiation' && (
          <VendorNegotiationTab data={negotiations} />
        )}
      </div>
    </div>
  )
}
