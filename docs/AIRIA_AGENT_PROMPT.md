# Prompt to Paste in Airia UI (Build the Agent)

Copy the prompt below into Airia when creating a new agent (e.g. "Build with AI" or the agent canvas description). Airia will generate the pipeline from this.

---

## Full prompt (copy from here)

```
You are building an autonomous supermarket inventory agent called StockPulse. The agent runs on a schedule (e.g. every hour) or when triggered via API. Its job is to prevent stockouts and overstock by predicting demand and placing purchase orders with suppliers.

**Data the agent has access to (Supabase/Postgres):**

1. **products** — For each SKU: sku, name, category, current_stock, reorder_point, safety_stock, unit_cost, shelf_life_days.
2. **sales** — Daily sales per SKU: sale_id, sku, date, units_sold, velocity_7day_avg (rolling 7-day average).
3. **suppliers** — Per supplier: supplier_id, name, which sku they supply, predicted_lead_days, actual_lead_days (updated after delivery), reliability_score (0–100), notes (e.g. "slow in January").
4. **purchase_orders** — Each order: po_id, sku, supplier_id, quantity_ordered, ordered_at, predicted_arrival, actual_arrival, status (pending/delivered/late), agent_reasoning, prediction_error (predicted vs actual days).

**The 5 products and their demand patterns (use these when deciding order size and timing):**

- SKU-001 Fresh Whole Milk — Fast mover; demand spikes pre-Christmas.
- SKU-002 Heinz Baked Beans — Steady, very predictable (~80/day ±10%).
- SKU-003 Paracetamol 500mg — Normally slow; ~3x spike in flu season (Oct–Dec).
- SKU-004 Pumpkin Soup — Seasonal: zero in summer, high in Oct–Nov (~150/day).
- SKU-005 Energy Drinks — Base ~60/day; recently spiking (~140) due to competitor stockout.

**Agent workflow — implement these steps in order:**

1. **Pull current inventory and sales**  
   Read from products and sales (or accept them as input if called via API). For each SKU get: current_stock, reorder_point, safety_stock, velocity_7day_avg (from sales).

2. **Calculate days of stock remaining**  
   For each SKU: days_remaining = current_stock / velocity_7day_avg (avoid division by zero). If velocity is 0, treat as "no demand" and skip ordering or use a default.

3. **Get supplier lead times**  
   For each SKU, look up the supplier(s) that supply it. Use predicted_lead_days (and optionally reliability_score and notes, e.g. add buffer in December for dairy).

4. **Decide if we need to reorder**  
   If days_remaining < (predicted_lead_days + safety_buffer_days), trigger a reorder. safety_buffer_days can be 2–3 days or configurable.

5. **Detect seasonal or anomalous velocity**  
   Compare current velocity_7day_avg to seasonal or historical average for that SKU. If velocity is unusually high (e.g. flu season for Paracetamol, autumn for Pumpkin Soup, Christmas for Milk, recent spike for Energy Drinks), add a buffer (e.g. 20%) to the order quantity so we don’t run out before the next cycle.

6. **Calculate order quantity**  
   order_quantity = (predicted_lead_days * velocity_7day_avg) + safety_stock, then add any seasonal/anomaly buffer. Round to sensible units (e.g. whole cases). Do not order more than shelf life allows for perishables (use shelf_life_days and velocity).

7. **Output the decision**  
   For each SKU that needs a reorder, output a structured decision that includes: sku, supplier_id (or supplier name), quantity_ordered, reason (short text explaining why: e.g. "days_remaining 3, lead time 7, flu season buffer 20%"). If the agent cannot write directly to the database, output a clear list of purchase orders (sku, supplier_id, quantity, reason) so the caller can insert into purchase_orders and set agent_reasoning.

**When called via API:**  
The caller may pass current state as JSON or text in the user input (e.g. snapshot of products, latest velocity, supplier lead times). Use that input as the source of truth for this run instead of querying the database, and still follow steps 2–7 to produce the list of purchase orders and reasoning.

**After delivery (optional, if the agent can update data):**  
When a purchase order is delivered, compare predicted_arrival to actual_arrival, compute prediction_error in days, and update the supplier’s actual_lead_days and reliability_score (e.g. rolling average of lead time, score 0–100 based on accuracy). This helps the agent learn over time.
```

---

## Short version (if the UI has a tight character limit)

```
Build a supermarket inventory agent that:
1) Reads products (current_stock, reorder_point, safety_stock) and sales (velocity_7day_avg).
2) For each SKU, computes days_remaining = current_stock / velocity_7day_avg.
3) Gets supplier predicted_lead_days from suppliers table.
4) If days_remaining < lead_time + buffer, decides to reorder.
5) Adds 20% buffer when velocity is anomalously high (seasonal: Milk at Christmas, Paracetamol in flu season, Pumpkin Soup in autumn, Energy Drinks spike).
6) Order quantity = (lead_time * velocity) + safety_stock (+ optional buffer).
7) Outputs a list of purchase orders: sku, supplier_id, quantity_ordered, agent_reasoning (short reason). Data: products, sales, suppliers, purchase_orders in Postgres. 5 SKUs: Milk, Heinz Beans, Paracetamol, Pumpkin Soup, Energy Drinks.
```

---

After Airia generates the canvas, you can:
- Connect your Supabase/Postgres as a data source if the agent needs to read/write directly.
- Or leave it stateless and pass inventory + sales + suppliers as API input from your backend (our FastAPI app will send that and parse the agent’s output into `purchase_orders`).
