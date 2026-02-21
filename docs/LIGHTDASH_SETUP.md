# Lightdash setup for StockPulse (step-by-step)

This guide uses the **Lightdash YAML** approach (no dbt required). You define models in YAML, deploy with the Lightdash CLI, then connect Supabase in the Lightdash UI.

---

## Prerequisites

- Supabase project with tables: `products`, `sales`, `suppliers`, `purchase_orders`, `agent_cycles` (run `backend/supabase_schema.sql` in Supabase SQL Editor if needed).
- A [Lightdash](https://lightdash.com) account (Cloud or self-hosted).
- Node.js 18+ (for the Lightdash CLI).

---

## How data works (important)

**No data is pushed or stored in Lightdash.** Lightdash connects to your **warehouse** (Supabase Postgres) and runs queries **live** against it. What you see in Lightdash is exactly what is in your Supabase database at query time. So “data in Lightdash” = data in Supabase (nothing is synced or copied into Lightdash).

So to see data in Lightdash you need:

1. **Warehouse connected** in Lightdash (Step 4): Project settings → Warehouse → Postgres with your Supabase host, user, password, database, schema `public`.
2. **Data in Supabase**: Tables must exist and have rows. Run `backend/supabase_schema.sql` in the Supabase SQL Editor to create tables and seed 5 products. More data (sales, POs, agent_cycles) appears when you use the StockPulse app (run cycles, etc.).

---

## Step 1: Install the Lightdash CLI

```bash
npm install -g @lightdash/cli
```

Or with npx (no global install):

```bash
npx @lightdash/cli --version
```

---

## Step 2: Log in to Lightdash

1. Go to [app.lightdash.com](https://app.lightdash.com) (or [eu1.lightdash.cloud](https://eu1.lightdash.cloud)) and sign in.
2. In the CLI, run:

```bash
lightdash login
```

This opens a browser to authenticate the CLI with your Lightdash account.

---

## Step 3: Deploy the StockPulse Lightdash project (create project)

Run the deploy from **inside the lightdash project folder** (the CLI reads `lightdash.config.yml` from the current directory):

```bash
cd /Users/j_kanishkha/stock-pulse/lightdash
lightdash deploy --create --no-warehouse-credentials
```

- `--create` creates a new Lightdash project.
- `--no-warehouse-credentials` means you will add the database connection in the Lightdash UI (recommended so you don’t put Supabase credentials in the CLI).

When prompted, choose your organization and give the project a name (e.g. **StockPulse**).

After this, your project exists in Lightdash and has the models from `lightdash/models/*.yml` (products, sales, purchase_orders, agent_cycles, suppliers).

---

## Step 4: Connect Supabase as the warehouse in Lightdash

1. In Lightdash, open the **StockPulse** project.
2. Go to **Project settings** (gear icon, top right).
3. Under **Warehouse connection**, click **Edit** or **Set up connection**.
4. Choose **Postgres**.
5. Fill in your **Supabase** database details:

   | Field    | Where to get it (Supabase Dashboard) |
   |----------|--------------------------------------|
   | Host     | **Project Settings → Database → Host** (e.g. `db.xxxx.supabase.co`) |
   | Port     | `5432` (or `6543` for connection pooler) |
   | User     | `postgres` (or a read-only user you create) |
   | Password | **Project Settings → Database → Database password** |
   | DB name  | `postgres` |
   | Schema   | `public` |

6. If you use **Lightdash Cloud**, Supabase may block the connection. In Supabase: **Project Settings → Database → Connection pooling** (or Network), add these IPs to the allow list:
   - `app.lightdash.cloud`: **35.245.81.252**
   - `eu1.lightdash.cloud`: **34.79.239.130**  
   (Or check the IP shown in Lightdash project settings.)
7. Save the connection. Lightdash will run a quick test query.

---

## How to check your Lightdash dashboard

1. **Open Lightdash:** [https://app.lightdash.com](https://app.lightdash.com) (US) or [https://eu1.lightdash.cloud](https://eu1.lightdash.cloud) (EU).
2. **Sign in** (Google, email, or SSO).
3. **Open your project** — e.g. **StockPulse** (click it in the project list or sidebar).
4. **Explore** — Pick a model (e.g. **products**, **sales**, **purchase_orders**), add dimensions/metrics, click **Run** to see data. Use **Save** to add the chart to a dashboard.
5. **Dashboards** — In the sidebar, open **Dashboards** and click a dashboard (e.g. “StockPulse Overview”) to see all saved charts.
6. **No tables?** Go to **Project settings** (gear) → **Warehouse** and confirm Supabase is connected, then click **Refresh dbt**.

---

## Step 5: Refresh and explore

1. In the project, open **Explore** (or **Query from tables**).
2. If you don’t see tables, click **Refresh dbt** (for YAML projects this syncs the deployed models).
3. You should see: **products**, **sales**, **purchase_orders**, **agent_cycles**, **suppliers**.
4. Select a table, pick dimensions and metrics, and build a chart.

---

## Step 6: Build the 6 StockPulse charts (from idea.md)

| Chart | How in Lightdash |
|-------|-------------------|
| **1. Inventory level timeline** | Explore **sales** (or a view joining products + sales). Line chart: date on X, `current_stock` or `velocity_7day_avg` by `sku`. Filter last 30 days. |
| **2. Days of stock remaining** | Explore **products**. Table: sku, name, current_stock, reorder_point. Add a calculated field or use conditional formatting (green / amber / red) based on stock level. |
| **3. Purchase orders timeline** | Explore **purchase_orders**. Bar chart: `ordered_at` (by day) on X, count or `quantity_ordered` sum on Y. |
| **4. Lead time: predicted vs actual** | Explore **purchase_orders** (and **suppliers** if joined). Bar chart: supplier or cycle on X, `prediction_error` or predicted vs actual days. |
| **5. Seasonal velocity patterns** | Explore **sales**. Line chart: date (by month) on X, `velocity_7day_avg` or `units_sold` by `sku`. |
| **6. Stockouts avoided / value saved** | Use **agent_cycles** (e.g. `accuracy`, cycle count) and/or **purchase_orders**; create a dashboard with single-number tiles. |

Save each chart to a **Dashboard** (e.g. “StockPulse Overview”).

---

## Updating the Lightdash project after changes

If you edit YAML files under `lightdash/models/`:

```bash
cd /Users/j_kanishkha/stock-pulse/lightdash
lightdash deploy --no-warehouse-credentials
```

Then in Lightdash, click **Refresh dbt** so the project picks up the new or changed models.

---

## Check if data is in Supabase (and thus visible in Lightdash)

Run from the repo root (with `SUPABASE_URL` and `SUPABASE_KEY` in `.env`):

```bash
python backend/check_supabase_data.py
```

This prints row counts for `products`, `sales`, `suppliers`, `purchase_orders`, and `agent_cycles`. If those tables have rows, Lightdash will show the same data when you open Explore and run a query (no separate “push to Lightdash” step).

---

## Troubleshooting

- **“No data” / empty results in Explore**
  - **Warehouse:** Confirm Project settings → Warehouse is set to Postgres with your **Supabase** credentials (host, user, password, db `postgres`, schema `public`). Test the connection.
  - **Data in Supabase:** In Supabase go to **Table Editor** and check that `products` (and other tables) have rows. If tables are empty, run `backend/supabase_schema.sql` in the SQL Editor (creates tables + 5 product rows).
  - **In Lightdash:** Open **Explore** → select a model (e.g. **products**) → add dimensions (e.g. sku, name, current_stock) → click **Run**. You should see rows from Supabase.

- **“No tables” or empty explores**  
  - Confirm the warehouse connection works (test from Project settings).  
  - Ensure Supabase has the tables in `public` and that the user has `SELECT` on them.  
  - Click **Refresh dbt** after deploying.

- **Connection refused / timeout from Lightdash Cloud**  
  - Allow Lightdash’s IPs in Supabase (see Step 4).  
  - Or use **Supabase connection pooler** (port 6543) if recommended for your plan.

- **CLI: “Not logged in”**  
  - Run `lightdash login` again and complete the browser flow.

- **Validate YAML locally**  
  - Run `lightdash lint` in the repo root to check for YAML errors before deploying.

---

## Summary

| Step | Action |
|------|--------|
| 1 | `npm install -g @lightdash/cli` |
| 2 | `lightdash login` |
| 3 | `cd lightdash` then `lightdash deploy --create --no-warehouse-credentials` |
| 4 | In Lightdash UI: Project settings → Warehouse → Postgres → Supabase host, user, password, dbname, schema `public` |
| 5 | Refresh and build charts from the 5 models (products, sales, purchase_orders, agent_cycles, suppliers) |

The `lightdash/` folder in this repo is the full Lightdash YAML project; you don’t need a separate dbt project.
