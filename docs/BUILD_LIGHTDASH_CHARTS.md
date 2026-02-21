# Building the 6 StockPulse Charts in Lightdash

Step-by-step guide to create each chart in the Lightdash UI. Ensure you’ve completed [LIGHTDASH_SETUP.md](LIGHTDASH_SETUP.md) (project created, Supabase connected, **Refresh dbt** done so new models appear).

---

## Chart 1 — Inventory Level Timeline

**Goal:** Line chart, one line per SKU, last 30 days. Shows which products are dropping fast.

1. In Lightdash, open **Explore** and select the **inventory_level_timeline** model.
2. **Dimensions:** `stock_date`, `sku` (or `name`).
3. **Metrics:** `stock_level` (or use the dimension as the value — pick **Stock level**).
4. **Chart type:** **Line chart**.
5. **X-axis:** `stock_date` (group by **Day**).
6. **Series / breakdown:** `sku` (one line per SKU).
7. **Y-axis:** `stock_level` (sum or raw).
8. **Filter:** Add filter `stock_date` **is in the past** **30 days** (or set a fixed date range).
9. **Run** and **Save** to a dashboard (e.g. “StockPulse Overview”). Name the chart “Inventory Level Timeline”.

---

## Chart 2 — Days of Stock Remaining (Traffic Lights)

**Goal:** Table with traffic lights. Green = 14+ days, Amber = 7–14, Red = under 7. Updates when Airia runs (data comes from `products`, which your app updates).

1. Open **Explore** and select **products**.
2. **Dimensions:** `sku`, `name`, `days_remaining`, `days_remaining_status`.
3. **Chart type:** **Table**.
4. **Conditional formatting (traffic lights):**
   - In the table settings, look for **Conditional formatting** or **Format**.
   - For the `days_remaining_status` column (or `days_remaining`):
     - **Green** when `days_remaining_status` = `Green` or `days_remaining` ≥ 14.
     - **Amber** when `days_remaining_status` = `Amber` or 7 ≤ `days_remaining` < 14.
     - **Red** when `days_remaining_status` = `Red` or `days_remaining` < 7.
   - If your Lightdash version uses rules: add a rule for each color based on the dimension value.
5. **Save** as “Days of Stock Remaining”.

*Note:* If there’s no conditional formatting UI, the `days_remaining_status` column still gives Green/Amber/Red as text so the table is readable.

---

## Chart 3 — Purchase Orders Timeline

**Goal:** Bar chart of POs placed per day. Shows the agent is actively working.

1. Open **Explore** and select **purchase_orders**.
2. **Dimensions:** `ordered_at`.
3. **Metrics:** **Count of rows** or **Total units ordered** (`total_units_ordered`) — for “POs per day”, count is best.
4. **Chart type:** **Bar chart**.
5. **X-axis:** `ordered_at` (group by **Day**).
6. **Y-axis:** Count of purchase orders (or **Total units ordered**).
7. **Filter (optional):** Last 30 or 90 days on `ordered_at`.
8. **Run** and **Save** as “Purchase Orders Timeline”.

---

## Chart 4 — Lead Time: Predicted vs Actual

**Goal:** Bar chart per supplier (and optionally per cycle). The gap between predicted and actual closes over time (learning proof).

1. Open **Explore** and select **purchase_orders**.
2. **Dimensions:** `supplier_id`, `ordered_at` (e.g. by week or month for “per cycle”).
3. **Metrics:** `avg_predicted_lead_days`, `avg_actual_lead_days` (or use dimensions `predicted_lead_days`, `actual_lead_days` and aggregate).
4. **Chart type:** **Bar chart** (grouped or stacked).
   - **X-axis:** `supplier_id` (or time period if you want “per cycle”).
   - **Y-axis:** Two series — **Predicted lead (days)** and **Actual lead (days)**.
5. Add both **Predicted lead days** and **Actual lead days** as metrics/series so you see two bars per supplier (or per period).
6. **Filter:** Optionally restrict to delivered POs only (`status` = `delivered`) so `actual_lead_days` is not null.
7. **Save** as “Lead Time: Predicted vs Actual”.

---

## Chart 5 — Seasonal Velocity Patterns

**Goal:** Line chart of sales velocity per SKU per month. Paracetamol line spikes in October; Pumpkin Soup flat then spike in autumn.

1. Open **Explore** and select **sales_velocity_monthly**.
2. **Dimensions:** `sale_month`, `sku`.
3. **Metrics:** `velocity_avg` or `total_units` (`units_sold_total`).
4. **Chart type:** **Line chart**.
5. **X-axis:** `sale_month` (by **Month**).
6. **Series:** `sku` (one line per SKU).
7. **Y-axis:** `velocity_avg` or **Total units sold**.
8. **Run** and **Save** as “Seasonal Velocity Patterns”.

*Alternative:* Use the **sales** model with `sale_month` and `sku`, and metric **Avg 7-day Velocity** (`avg_velocity` on `velocity_7day_avg`) or **Total units sold**, then group by month and SKU.

---

## Chart 6 — Stockouts Avoided + Value Saved

**Goal:** Single-number cards: “X stockouts avoided this month” and “£X in lost sales prevented” (or value replenished).

1. Open **Explore** and select **stockouts_avoided_metrics**.
2. This model has one row with:
   - `stockouts_avoided_this_month` — number of POs (replenishment orders) this month.
   - `value_saved_gbp` — value of inventory replenished this month (£).
3. **Chart type:** **Big number** or **Single value**.
4. **First tile:** Use metric **Stockouts avoided (this month)** or the dimension `stockouts_avoided_this_month`. Title: “Stockouts avoided this month”.
5. **Second tile:** Use metric **Value Saved (£)** or dimension `value_saved_gbp`. Title: “Value saved / replenished (£)”.
   - Format as currency if the UI allows.
6. **Save** as “Stockouts Avoided & Value Saved”.

*Note:* “Value saved” here is the value of inventory replenished (quantity × unit cost). To show “lost sales prevented” you’d need a separate metric (e.g. estimated lost units × price) — you can add that later as a custom metric or new model.

---

## Quick reference

| Chart | Model | Chart type | X-axis | Series / breakdown | Y / value |
|-------|--------|------------|--------|--------------------|-----------|
| 1. Inventory timeline | inventory_level_timeline | Line | stock_date (day) | sku | stock_level |
| 2. Days remaining | products | Table | — | — | sku, name, days_remaining, days_remaining_status |
| 3. POs timeline | purchase_orders | Bar | ordered_at (day) | — | Count or total_units_ordered |
| 4. Lead time | purchase_orders | Bar | supplier_id (or time) | — | predicted_lead_days, actual_lead_days |
| 5. Seasonal velocity | sales_velocity_monthly | Line | sale_month | sku | velocity_avg or units_sold_total |
| 6. Stockouts / value | stockouts_avoided_metrics | Big number | — | — | stockouts_avoided_this_month, value_saved_gbp |

---

## After changing models

If you edit or add models under `lightdash/models/`:

```bash
cd lightdash
lightdash deploy --no-warehouse-credentials
```

Then in Lightdash click **Refresh dbt** so the new or updated models and columns appear in Explore.
