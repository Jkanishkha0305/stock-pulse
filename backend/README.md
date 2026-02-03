# StockPulse Backend

FastAPI server with Supabase and Airia integration.

## Setup

1. Copy `.env.example` to `.env` and set:
   - **SUPABASE_URL** — From Supabase project Settings > API > Project URL.
   - **SUPABASE_KEY** — Use the **anon (public)** key from Settings > API (long JWT starting with `eyJ...`). The service role key also works but has full access.
   - **AIRIA_WEBHOOK_URL** — From Airia Agent Studio > Settings > Interfaces > View API Info.
   - **AIRIA_API_KEY** — From the same place or Settings > API Keys.

2. If your Supabase project has no tables yet, run `supabase_schema.sql` in the Supabase SQL Editor (Dashboard > SQL Editor).

3. Install and run (use the same Python for both so dependencies are found):
   ```bash
   cd backend
   python3 -m pip install -r requirements.txt
   python3 -m uvicorn main:app --reload --port 8000
   ```
   If you see `ModuleNotFoundError: No module named 'httpx'`, your `python3` and `uvicorn` are from different environments. Use `python3 -m uvicorn` (as above) so the interpreter that has the packages is used.

## Endpoints

- `GET /api/dashboard` — Products, cycle index, accuracy, activities.
- `POST /api/run-cycle` — Run agent cycle (prioritize, signals, Airia, vendor negotiation, place POs).
- `GET /api/activity` — Recent purchase orders.
- `GET /api/vendor-negotiation` — Latest run’s vendor conversations.
- `GET /health` — Health check.

When Supabase credentials are missing or invalid, the backend uses in-memory demo data so the app still runs.
