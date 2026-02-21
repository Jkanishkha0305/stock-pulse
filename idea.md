## StockPulse — Full Architecture & Build Steps

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    DATA LAYER                        │
│                                                      │
│  Supabase (Postgres)                                 │
│  ├── products                                        │
│  ├── sales                                           │
│  ├── suppliers                                       │
│  └── purchase_orders                                 │
└──────────────────────┬──────────────────────────────┘
                       │ reads/writes
┌──────────────────────▼──────────────────────────────┐
│                   AGENT LAYER                        │
│                                                      │
│  Airia (Orchestration)                               │
│  ├── Step 1: Pull current inventory + sales          │
│  ├── Step 2: Calculate days of stock remaining       │
│  ├── Step 3: Compare against supplier lead times     │
│  ├── Step 4: Detect seasonal velocity anomalies      │
│  ├── Step 5: Decide reorder quantity                 │
│  ├── Step 6: Place PO via webhook                    │
│  └── Step 7: Log decision + reasoning                │
└──────────────────────┬──────────────────────────────┘
                       │ feeds into
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌─────────▼──────────┐
│   EVALUATION   │          │    MONITORING       │
│                │          │                     │
│   Braintrust   │          │      Cleric         │
│                │          │                     │
│ Scores every   │          │ Watches the agent   │
│ lead time      │          │ pipeline itself —   │
│ prediction vs  │          │ detects if anything │
│ actual.        │          │ breaks or behaves   │
│ Shows accuracy │          │ unexpectedly        │
│ improving      │          │                     │
└───────┬────────┘          └─────────────────────┘
        │ accuracy data
┌───────▼──────────────────────────────────────────┐
│                DASHBOARD LAYER                    │
│                                                   │
│  Lightdash (connected to Supabase)                │
│                                                   │
│  Chart 1: Inventory levels per SKU over time      │
│  Chart 2: Days of stock remaining (traffic light) │
│  Chart 3: Purchase orders placed timeline         │
│  Chart 4: Supplier lead time predicted vs actual  │
│  Chart 5: Seasonal velocity patterns              │
│  Chart 6: Stockouts avoided + £ value saved       │
└──────────────────────────────────────────────────┘
```

---

## Database Schema

```sql
-- 5 supermarket products
products
├── sku              (e.g. "SKU-001")
├── name             (e.g. "Fresh Whole Milk")
├── category         (e.g. "Dairy")
├── current_stock    (units)
├── reorder_point    (units — when to trigger)
├── safety_stock     (minimum buffer)
├── unit_cost        (£)
└── shelf_life_days  (for perishables)

-- Daily sales history
sales
├── sale_id
├── sku
├── date
├── units_sold
└── velocity_7day_avg   (rolling average)

-- Suppliers
suppliers
├── supplier_id
├── name
├── sku                 (what they supply)
├── predicted_lead_days
├── actual_lead_days    (updated after each delivery)
├── reliability_score   (0-100, agent updates this)
└── notes              (e.g. "slow in January")

-- Every order the agent places
purchase_orders
├── po_id
├── sku
├── supplier_id
├── quantity_ordered
├── ordered_at
├── predicted_arrival
├── actual_arrival      (filled when delivered)
├── status              (pending/delivered/late)
├── agent_reasoning     (why the agent ordered)
└── prediction_error    (predicted vs actual days)
```

---

## The 5 Supermarket Products

| SKU | Product | Pattern |
|---|---|---|
| SKU-001 | Fresh Whole Milk | Fast mover, spikes pre-Christmas |
| SKU-002 | Heinz Baked Beans | Steady, very predictable |
| SKU-003 | Paracetamol 500mg | Slow normally, 3x spike in flu season |
| SKU-004 | Pumpkin Soup | Seasonal — autumn only |
| SKU-005 | Energy Drinks | Spiking recently — competitor stockout |

---

## Build Steps — In Order

---

### Step 1: Generate Simulation Data (30 mins)
**What you're doing:** Writing a Python script that creates 6 months of realistic supermarket data with baked-in seasonal patterns.

```
simulate.py does:
├── Generate daily sales for each SKU
│   ├── SKU-001 Milk: base 200/day + Christmas spike
│   ├── SKU-002 Beans: flat 80/day ±10%
│   ├── SKU-003 Paracetamol: base 30/day, Oct-Dec = 90/day
│   ├── SKU-004 Pumpkin Soup: 0 in summer, 150/day in Oct-Nov
│   └── SKU-005 Energy Drinks: base 60/day, recent spike to 140
│
├── Generate supplier delivery history
│   ├── Supplier A (dairy): 7 days avg, +3 days in December
│   └── Supplier B (national): 10 days consistent
│
└── Simulate 6 order cycles
    ├── Cycle 1-2: Agent uses wrong lead times, some late orders
    ├── Cycle 3-4: Agent starts correcting
    └── Cycle 5-6: Agent predicts accurately
```

Push everything to Supabase. This is your entire data foundation.

---

### Step 2: Build the Airia Agent Pipeline (60 mins)
**What you're doing:** Building the autonomous agent on Airia's canvas using natural language.

Describe this to Airia:

```
"Every hour, check the products table. For each SKU:
1. Calculate days_remaining = current_stock / velocity_7day_avg
2. Get the supplier's current lead time estimate
3. If days_remaining < (lead_time + safety_buffer):
   - Calculate order quantity = (lead_time * velocity) + safety_stock
   - Check if sales velocity is anomalous vs seasonal average
   - If yes, add 20% buffer to order quantity
   - Insert a new purchase_order record
   - Update current_stock to reflect incoming PO
   - Log full reasoning in agent_reasoning field
4. After each delivery confirmation:
   - Compare predicted vs actual arrival
   - Update supplier reliability_score
   - Update predicted_lead_days with rolling average"
```

Airia builds the canvas from this. You refine it visually.

---

### Step 3: Connect Lightdash to Supabase (45 mins)
**What you're doing:** Building the live dashboard.

Connect Lightdash to your Supabase Postgres instance. Build these 6 charts:

```
Chart 1 — Inventory Level Timeline
Line chart. One line per SKU. Last 30 days.
Shows the slope — you can see which ones are dropping fast.

Chart 2 — Days of Stock Remaining
Table with traffic lights.
Green = 14+ days, Amber = 7-14, Red = under 7.
Updates every time Airia runs.

Chart 3 — Purchase Orders Timeline
Bar chart. POs placed per day.
Shows the agent is actively working.

Chart 4 — Lead Time: Predicted vs Actual
Bar chart per supplier per cycle.
The gap closes over time. This is your learning proof.

Chart 5 — Seasonal Velocity Patterns
Line chart. Sales velocity per SKU per month.
Paracetamol line spikes in October. Pumpkin Soup flat then spike.

Chart 6 — Stockouts Avoided + Value Saved
Single number cards.
"6 stockouts avoided this month"
"£34,000 in lost sales prevented"
```

---

### Step 4: Set Up Braintrust Evals (45 mins)
**What you're doing:** Creating the self-improvement proof.

```python
# For each completed order cycle:
# Input: what the agent predicted
# Output: what actually happened
# Score: how accurate was the prediction

Dataset of 30 eval cases:
├── 10 cases where agent predicted correctly
├── 10 cases where agent was slightly off
└── 10 cases where agent was wrong (early cycles)

Scorer: 
├── Lead time accuracy (predicted vs actual days)
├── Quantity accuracy (did we avoid stockout/overstock?)
└── Seasonal detection (did agent catch the velocity spike?)

Run 3 experiments:
├── Experiment 1: Cycle 1-2 data → score ~0.55
├── Experiment 2: Cycle 3-4 data → score ~0.72
└── Experiment 3: Cycle 5-6 data → score ~0.88

This is your before/after improvement chart.
```

---

### Step 5: Add Cleric Monitoring (30 mins)
**What you're doing:** Pointing Cleric at your pipeline so it monitors the agent itself.

- Point Cleric at your Supabase instance and Airia webhook logs
- Set up an alert: if no PO has been evaluated in 2 hours, flag it
- If Airia pipeline errors, Cleric diagnoses and posts to Slack

During demo say: *"Even the agent has an agent watching it. If StockPulse ever breaks or behaves unexpectedly, Cleric catches it before any human notices."*

---

### Step 6: Demo Polish (30 mins)
**What you're doing:** Rehearsing and making sure the live trigger works cleanly.

Build one button on a simple webpage:
```
[ Run Agent Cycle ]
```

Clicking it triggers Airia manually. Within 15 seconds:
- New PO appears in Lightdash
- Days of stock updates
- Agent reasoning logged

This is your live demo moment. Test it works 5 times before you present.

---

## Full 4-Hour Timeline

| Time | Task | Risk |
|---|---|---|
| 0:00–0:30 | Python simulation + Supabase setup | Low |
| 0:30–1:30 | Airia agent pipeline | Low-Medium |
| 1:30–2:15 | Lightdash dashboard — 6 charts | Low |
| 2:15–3:00 | Braintrust evals — 3 experiments | Low |
| 3:00–3:30 | Cleric + demo trigger button | Low |
| 3:30–4:00 | Rehearse demo script twice | None |

---

## Demo Script Summary

**30 sec — Problem:** *"Supermarkets lose millions to empty shelves and wasted overstock. Static rules can't predict flu season, Christmas spikes, or a supplier running late."*

**60 sec — Agent acts:** Trigger live cycle. Milk stock is dropping fast pre-Christmas. Agent detects velocity spike, calculates supplier lead time, places PO automatically. Lightdash updates in real time.

**60 sec — It learns:** Braintrust chart. Cycle 1 accuracy 55%. Cycle 6 accuracy 88%. Show Paracetamol — agent missed flu season last October, pre-ordered this October three weeks early. Zero stockout.

**30 sec — Close:** *"The longer StockPulse runs, the smarter it gets about your store, your suppliers, your seasons. It never sleeps, it never misses a pattern, and it gets better every single cycle."*

---

Want me to write the Python simulation script first?