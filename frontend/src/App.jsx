import { useState } from 'react'
import Dashboard from './components/Dashboard'
import VendorNegotiationTab from './components/VendorNegotiationTab'

const TABS = { dashboard: 'dashboard', vendor: 'vendor' }

function App() {
  const [tab, setTab] = useState(TABS.dashboard)

  return (
    <div className="app-shell min-h-screen">
      <main className="mx-auto max-w-[1280px] px-4 py-6 sm:px-6 lg:px-8">
        <header className="surface-card animate-lift mb-6 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="label-caps">Autonomous Supply Intelligence</p>
              <h1 className="font-display mt-2 text-2xl text-slate-50 sm:text-3xl">
                StockPulse Control Room
              </h1>
            </div>
            <div className="rounded-full border border-emerald-400/40 bg-emerald-400/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">
              Live System Ready
            </div>
          </div>

          <nav className="mt-5 inline-flex rounded-xl border border-slate-700/70 bg-slate-950/55 p-1">
            <TabButton
              active={tab === TABS.dashboard}
              onClick={() => setTab(TABS.dashboard)}
            >
              Mission Dashboard
            </TabButton>
            <TabButton
              active={tab === TABS.vendor}
              onClick={() => setTab(TABS.vendor)}
            >
              Vendor Negotiation
            </TabButton>
          </nav>
        </header>

        {tab === TABS.dashboard && (
          <Dashboard onNavigateToVendor={() => setTab(TABS.vendor)} />
        )}
        {tab === TABS.vendor && (
          <div className="animate-lift">
            <VendorNegotiationTab />
          </div>
        )}
      </main>
    </div>
  )
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
        active
          ? 'bg-slate-800 text-emerald-300 shadow-inner shadow-emerald-500/20'
          : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-200'
      }`}
    >
      {children}
    </button>
  )
}

export default App
