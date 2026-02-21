import { useState } from 'react'

const DEMO_NEGOTIATIONS = [
  {
    sku: 'SKU-001', sku_name: 'Fresh Whole Milk', quantity: 1540,
    chosen_offer: { vendor_id: 'SUPPLIER-A', vendor_name: 'FreshFarm Dairy', price_per_unit: 0.81, total_gbp: 1247.40, lead_days: 6 },
    conversations: [
      {
        vendor_id: 'SUPPLIER-A', vendor_name: 'FreshFarm Dairy', chosen: true,
        offer: { price_per_unit: 0.81, total_gbp: 1247.40, lead_days: 6, terms: 'Net 30' },
        messages: [
          { role: 'agent',  text: 'We need 1540 units of Fresh Whole Milk urgently. Can you quote?' },
          { role: 'vendor', text: 'Yes, we can supply. Our standard price is £0.85/unit, delivery in 7 days.' },
          { role: 'agent',  text: 'If we commit to 1540 units, can you do £0.81/unit and 6-day delivery?' },
          { role: 'vendor', text: 'Deal — £0.81/unit, £1,247.40 total, delivered in 6 days. Net 30.' },
        ],
      },
      {
        vendor_id: 'SUPPLIER-B', vendor_name: 'NationalDist Ltd', chosen: false,
        offer: { price_per_unit: 0.91, total_gbp: 1401.40, lead_days: 10, terms: 'Net 14' },
        messages: [
          { role: 'agent',  text: 'We need 1540 units of Fresh Whole Milk urgently. Can you quote?' },
          { role: 'vendor', text: 'We can deliver in 10 days at £0.91/unit. Total £1,401.40.' },
          { role: 'agent',  text: 'Can you match 7 days for £0.88/unit?' },
          { role: 'vendor', text: 'Minimum lead time is 10 days. Best price is £0.91/unit. Net 14.' },
        ],
      },
      {
        vendor_id: 'SUPPLIER-C', vendor_name: 'BulkBuy Wholesale', chosen: false,
        offer: { price_per_unit: 0.87, total_gbp: 1339.80, lead_days: 8, terms: 'Net 14' },
        messages: [
          { role: 'agent',  text: 'We need 1540 units of Fresh Whole Milk urgently. Can you quote?' },
          { role: 'vendor', text: 'We have stock. £0.89/unit, delivery in 8 days.' },
          { role: 'agent',  text: 'Order of 1540 — can you do £0.87 and 7 days?' },
          { role: 'vendor', text: '£0.87/unit accepted. Lead time is 8 days minimum. Final.' },
        ],
      },
    ],
  },
  {
    sku: 'SKU-003', sku_name: 'Paracetamol 500mg', quantity: 470,
    chosen_offer: { vendor_id: 'SUPPLIER-B', vendor_name: 'NationalDist Ltd', price_per_unit: 2.31, total_gbp: 1085.70, lead_days: 10 },
    conversations: [
      {
        vendor_id: 'SUPPLIER-A', vendor_name: 'FreshFarm Dairy', chosen: false,
        offer: { price_per_unit: 2.20, total_gbp: 1034.00, lead_days: 14, terms: 'Net 30' },
        messages: [
          { role: 'agent',  text: 'Need 470 units Paracetamol 500mg — flu season spike detected.' },
          { role: 'vendor', text: 'We can source it but lead time is 14 days. £2.20/unit.' },
          { role: 'agent',  text: 'Stock critically low. Can you expedite to 10 days?' },
          { role: 'vendor', text: 'Sorry, 14 days is our minimum for pharma. £2.20/unit, final.' },
        ],
      },
      {
        vendor_id: 'SUPPLIER-B', vendor_name: 'NationalDist Ltd', chosen: true,
        offer: { price_per_unit: 2.31, total_gbp: 1085.70, lead_days: 10, terms: 'Net 14' },
        messages: [
          { role: 'agent',  text: 'Need 470 units Paracetamol 500mg — flu season spike detected.' },
          { role: 'vendor', text: 'Paracetamol 500mg in stock. £2.40/unit, 10-day delivery.' },
          { role: 'agent',  text: 'Bulk order of 470 — can you do £2.31/unit?' },
          { role: 'vendor', text: 'Agreed. £2.31/unit × 470 = £1,085.70. 10 days. Net 14.' },
        ],
      },
      {
        vendor_id: 'SUPPLIER-C', vendor_name: 'BulkBuy Wholesale', chosen: false,
        offer: { price_per_unit: 2.38, total_gbp: 1118.60, lead_days: 9, terms: 'Net 14' },
        messages: [
          { role: 'agent',  text: 'Need 470 units Paracetamol 500mg — flu season spike detected.' },
          { role: 'vendor', text: '£2.45/unit, 9-day delivery from our warehouse.' },
          { role: 'agent',  text: 'Can you match £2.35 given the volume?' },
          { role: 'vendor', text: 'Best we can do is £2.38/unit. £1,118.60 total. Final.' },
        ],
      },
    ],
  },
]

function ChatBubble({ msg }) {
  const isAgent = msg.role === 'agent'
  return (
    <div className={`flex ${isAgent ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[88%] px-3 py-2 rounded-xl text-xs leading-relaxed terminal ${
        isAgent
          ? 'bg-[#41d6ad]/12 text-[#41d6ad] border border-[#41d6ad]/20 rounded-tr-sm'
          : 'bg-white/5 text-slate-300 border border-white/8 rounded-tl-sm'
      }`}>
        <span className={`block text-[9px] mb-0.5 ${isAgent ? 'text-[#41d6ad]/50' : 'text-slate-600'}`}>
          {isAgent ? 'AGENT' : 'VENDOR'}
        </span>
        {msg.text}
      </div>
    </div>
  )
}

function VendorColumn({ conv }) {
  return (
    <div className={`flex flex-col rounded-xl overflow-hidden border ${
      conv.chosen ? 'border-[#41d6ad]/25' : 'border-white/8'
    }`}
      style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
        boxShadow: conv.chosen ? '0 0 0 1px rgba(65,214,173,0.1), 0 0 24px rgba(65,214,173,0.07)' : undefined,
      }}
    >
      {/* Header */}
      <div className={`px-4 py-3 border-b ${conv.chosen ? 'border-[#41d6ad]/15 bg-[#41d6ad]/5' : 'border-white/6'}`}>
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="text-[10px] text-slate-500 font-mono">{conv.vendor_id}</p>
            <p className="text-sm font-semibold text-slate-200 truncate">{conv.vendor_name}</p>
          </div>
          {conv.chosen
            ? <span className="shrink-0 px-2 py-0.5 rounded-full bg-[#41d6ad]/15 border border-[#41d6ad]/30 text-[#41d6ad] text-[10px] font-mono font-semibold">★ WINNER</span>
            : <span className="shrink-0 text-[10px] text-slate-600 font-mono">—</span>
          }
        </div>
      </div>

      {/* Chat */}
      <div className="p-3 overflow-y-auto" style={{ maxHeight: 220 }}>
        {conv.messages.map((msg, i) => <ChatBubble key={i} msg={msg} />)}
      </div>

      {/* Offer summary */}
      <div className={`px-4 py-3 border-t ${conv.chosen ? 'border-[#41d6ad]/15 bg-[#41d6ad]/5' : 'border-white/5 bg-white/2'}`}>
        <div className="grid grid-cols-3 gap-2 text-center">
          {[
            { label: 'Price/unit', value: `£${conv.offer.price_per_unit}` },
            { label: 'Total',      value: `£${conv.offer.total_gbp?.toLocaleString()}` },
            { label: 'Lead time',  value: `${conv.offer.lead_days}d` },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-[9px] text-slate-500">{label}</p>
              <p className={`text-sm font-bold font-mono ${conv.chosen ? 'text-[#41d6ad]' : 'text-slate-300'}`}>{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function NegotiationGroup({ neg }) {
  const maxTotal = Math.max(...(neg.conversations?.map(c => c.offer.total_gbp) || [0]))
  const winTotal = neg.chosen_offer?.total_gbp || 0
  const saved = maxTotal - winTotal

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div>
          <p className="text-xs text-slate-500 font-mono">{neg.sku}</p>
          <h3 className="text-base font-semibold text-slate-200">{neg.sku_name}</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {neg.quantity?.toLocaleString()} units · Winner:
            <span className="text-[#41d6ad] ml-1">{neg.chosen_offer?.vendor_name}</span>
          </p>
        </div>
        {saved > 0 && (
          <div className="px-3 py-1.5 rounded-full bg-[#f4bf4f]/10 border border-[#f4bf4f]/20">
            <span className="text-[#f4bf4f] text-xs font-mono font-semibold">
              💰 Saved £{Math.round(saved).toLocaleString()} vs highest bid
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {neg.conversations?.map(conv => (
          <VendorColumn key={conv.vendor_id} conv={conv} />
        ))}
      </div>
    </div>
  )
}

export default function VendorNegotiationTab({ data }) {
  const negotiations = data?.negotiations?.length ? data.negotiations : DEMO_NEGOTIATIONS

  return (
    <div>
      <div className="glass-card p-4 flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
            <span className="w-1 h-4 rounded-full bg-[#f4bf4f] inline-block" />
            Vendor Negotiation Engine
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Agent simultaneously negotiates with 3 vendors in real-time — picks best price × lead time
          </p>
        </div>
        <div className="flex gap-6 text-center">
          <div>
            <p className="text-xl font-bold text-[#f4bf4f] text-glow-amber font-display">3</p>
            <p className="text-[10px] text-slate-500">vendors / SKU</p>
          </div>
          <div>
            <p className="text-xl font-bold text-[#41d6ad] text-glow-mint font-display">
              £{negotiations.reduce((sum, n) => {
                const max = Math.max(...(n.conversations?.map(c => c.offer.total_gbp) || [0]))
                return sum + max - (n.chosen_offer?.total_gbp || 0)
              }, 0).toFixed(0)}
            </p>
            <p className="text-[10px] text-slate-500">saved this run</p>
          </div>
        </div>
      </div>

      {negotiations.map(neg => (
        <NegotiationGroup key={neg.sku} neg={neg} />
      ))}
    </div>
  )
}
