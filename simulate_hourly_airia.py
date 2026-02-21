"""
simulate_hourly_airia.py — 30-day, hourly ops simulator with Airia calls

What it does
- Simulates 30 days, hours 09:00–20:00 (11 ticks/day).
- Applies intra-day demand (splitting the daily demand curve).
- When stock drops below reorder_point, it triggers the Airia webhook
  (if AIRIA_WEBHOOK_URL is set). If Airia is unreachable, falls back
  to a simple reorder rule.
- Lead times are capped at 3 days to keep the short demo loop tight.
- Pending POs are delivered after their (simulated) actual lead time,
  adding stock and marking status=delivered.
- Writes every change to Supabase: sales rows, purchase_orders, product stock.

Run
  uv run simulate_hourly_airia.py
Env
  SIM_DAYS=30 (default)
  AIRIA_WEBHOOK_URL, AIRIA_API_KEY (optional; uses simple reorder if absent/fails)
  SUPABASE_URL, SUPABASE_KEY (required)
"""

import os
import random
import uuid
import json
from datetime import date, datetime, timedelta
from collections import defaultdict

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
AIRIA_WEBHOOK_URL = os.environ.get("AIRIA_WEBHOOK_URL")
AIRIA_API_KEY = os.environ.get("AIRIA_API_KEY")
SIM_DAYS = int(os.environ.get("SIM_DAYS", 30))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Demand model (copied from simulate.py)
def daily_units(sku: str, sale_date: date, days_ago: int) -> int:
    month = sale_date.month
    weekday = sale_date.weekday()
    if sku == "SKU-001":
        base = 200
        if month == 11:
            base = int(base * 1.20)
        elif month == 12:
            base = int(base * 1.40)
        noise = random.uniform(-0.15, 0.15)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-002":
        base = 80
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-003":
        base = 30
        if month == 10:
            base = int(base * 2.0)
        elif month == 11:
            base = int(base * 3.0)
        elif month == 12:
            base = int(base * 2.5)
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-004":
        if month in (6, 7, 8):
            return random.randint(3, 7)
        elif month == 9:
            return random.randint(45, 75)
        elif month == 10:
            return random.randint(130, 170)
        elif month == 11:
            return random.randint(100, 140)
        elif month == 12:
            return random.randint(30, 50)
        else:
            return random.randint(10, 20)
    elif sku == "SKU-005":
        base = 140 if days_ago <= 30 else 60
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-006":
        base = 120 if weekday < 5 else 90
        noise = random.uniform(-0.12, 0.12)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-007":
        base = 110
        if month in (3, 4):
            base = int(base * 1.25)
        noise = random.uniform(-0.08, 0.08)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-008":
        base = 190
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-009":
        base = 95
        if weekday in (4, 5):
            base = int(base * 1.20)
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-010":
        base = 210
        if month in (6, 7, 8):
            base = int(base * 1.30)
        noise = random.uniform(-0.08, 0.08)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-011":
        base = 70
        if month == 1:
            base = int(base * 1.35)
        noise = random.uniform(-0.12, 0.12)
        return max(1, int(base * (1 + noise)))
    elif sku == "SKU-012":
        base = 75
        if month == 1:
            base = int(base * 1.20)
        noise = random.uniform(-0.08, 0.08)
        return max(1, int(base * (1 + noise)))
    return 0


def load_products() -> dict:
    rows = supabase.table("products").select("*").execute().data
    return {r["sku"]: r for r in rows}


def load_suppliers() -> dict:
    rows = supabase.table("suppliers").select("*").execute().data
    mapping = {}
    for r in rows:
        mapping.setdefault(r["sku"], r)
    return mapping


def split_hourly(total: int, hours: int = 11) -> list[int]:
    """Split a daily total into hourly chunks with small randomness."""
    base = total // hours
    rem = total - base * hours
    chunks = [base] * hours
    for i in range(rem):
        chunks[i % hours] += 1
    # add slight jitter
    return [max(0, int(c * random.uniform(0.9, 1.1))) for c in chunks]


def try_airia_order(products, suppliers, sim_datetime):
    """Call Airia; must succeed. Parses multiple response shapes; errors only if truly empty/invalid."""
    if not AIRIA_WEBHOOK_URL or not AIRIA_API_KEY:
        raise RuntimeError("AIRIA_WEBHOOK_URL and AIRIA_API_KEY must be set (no fallback allowed).")

    def strip_fences(s: str) -> str:
        return s.replace("```json", "").replace("```", "").strip()

    def extract_orders(payload):
        # Accept list directly
        if isinstance(payload, list):
            return payload
        # Accept dict with common fields
        if isinstance(payload, dict):
            if isinstance(payload.get("orders"), list):  # allow status + orders wrapper
                return payload["orders"]
            if isinstance(payload.get("orders"), list):
                return payload["orders"]
            if isinstance(payload.get("purchase_orders"), list):
                return payload["purchase_orders"]
            # Try raw_output inside dict (often holds fenced JSON)
            if isinstance(payload.get("raw_output"), str):
                try:
                    inner_json = json.loads(strip_fences(payload["raw_output"]))
                    found = extract_orders(inner_json)
                    if found:
                        return found
                except Exception:
                    pass
            # Braintrust/Airia style nested result
            if isinstance(payload.get("result"), str):
                inner = payload["result"]
                try:
                    inner_json = json.loads(strip_fences(inner))
                    found = extract_orders(inner_json)
                    if found:
                        return found
                except Exception:
                    pass
            if isinstance(payload.get("result"), dict):
                found = extract_orders(payload["result"])
                if found:
                    return found
        # Accept stringified JSON (possibly fenced)
        if isinstance(payload, str):
            try:
                inner_json = json.loads(strip_fences(payload))
                found = extract_orders(inner_json)
                if found:
                    return found
            except Exception:
                pass
        return []

    payload = {
        "UserInput": f"Stock snapshot {sim_datetime.isoformat()}",
        "products": [
            {
                "sku": sku,
                "current_stock": p["current_stock"],
                "reorder_point": p["reorder_point"],
                "safety_stock": p["safety_stock"],
                "daily_velocity": p.get("daily_velocity"),
            }
            for sku, p in products.items()
        ],
        "suppliers": list(suppliers.values()),
    }
    resp = requests.post(
        AIRIA_WEBHOOK_URL,
        headers={"Content-Type": "application/json", "X-Api-Key": AIRIA_API_KEY},
        data=json.dumps(payload),
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Airia returned {resp.status_code}: {resp.text[:200]}")

    # Try JSON first; if that fails, attempt to parse text as JSON after stripping fences
    try:
        raw = resp.json()
    except Exception:
        raw = strip_fences(resp.text)

    orders = extract_orders(raw)
    if not orders:
        # No orders parsed; log and continue (no fallback ordering).
        print(f"[WARN] Airia returned no parsable orders at {sim_datetime}: sample={str(raw)[:200]}")
        return []
    return orders


def simulate():
    if not AIRIA_WEBHOOK_URL or not AIRIA_API_KEY:
        raise SystemExit("AIRIA_WEBHOOK_URL and AIRIA_API_KEY required for this simulator (no fallback).")

    products = load_products()
    suppliers = load_suppliers()
    demand_history: dict[str, list[int]] = defaultdict(list)
    pending = []

    today = date.today()
    hours = list(range(9, 21))  # 09:00–20:00 inclusive

    for day in range(1, SIM_DAYS + 1):
        sim_date = today + timedelta(days=day)
        print(f"Day {day}/{SIM_DAYS} — {sim_date}")

        for hour in hours:
            sim_dt = datetime.combine(sim_date, datetime.min.time()) + timedelta(hours=hour)
            # 1) Hourly demand
            sales_batch = []
            for sku, prod in products.items():
                daily = daily_units(sku, sim_date, days_ago=0)
                hourly_demands = split_hourly(daily, len(hours))
                demand = hourly_demands[hour - hours[0]]
                sold = min(prod["current_stock"], demand)
                prod["current_stock"] = max(0, prod["current_stock"] - sold)
                demand_history[sku].append(demand)
                # rolling velocity approx with last 7 days of totals
                last7 = demand_history[sku][-7*len(hours):]
                velocity = round(sum(last7) / 7, 2) if last7 else 0.0
                sales_batch.append({
                    "sku": sku,
                    "date": sim_date.isoformat(),
                    "units_sold": sold,
                    "velocity_7day_avg": velocity,
                })
                prod["daily_velocity"] = velocity

            if sales_batch:
                supabase.table("sales").insert(sales_batch).execute()

            # 2) Deliver due POs
            for po in list(pending):
                if sim_dt.date() >= po["due_date"]:
                    actual_lead = (sim_dt.date() - po["ordered_date"]).days
                    prediction_error = po["predicted_lead_days"] - actual_lead
                    supabase.table("purchase_orders").update({
                        "status": "delivered",
                        "actual_arrival": sim_dt.date().isoformat(),
                        "prediction_error": prediction_error,
                        "stockout_days": po["stockout_days"],
                    }).eq("po_id", po["po_id"]).execute()
                    products[po["sku"]]["current_stock"] += po["quantity_ordered"]
                    pending.remove(po)

            # 3) Trigger Airia once per hour if any SKU below reorder_point
            needs_reorder = [sku for sku, p in products.items() if p["current_stock"] < p["reorder_point"]]
            if needs_reorder:
                orders = try_airia_order(products, suppliers, sim_dt)

                for o in orders:
                    sku = o["sku"]
                    sup = suppliers.get(sku, {})
                    predicted_lead = min(3, int(o.get("predicted_lead_days") or sup.get("predicted_lead_days", 2)))
                    actual_lead = min(3, int(o.get("actual_lead_days") or sup.get("actual_lead_days", predicted_lead)))
                    po_id = str(uuid.uuid4())
                    ordered_at = sim_dt.isoformat()
                    predicted_arrival = o.get("predicted_arrival") or (sim_dt.date() + timedelta(days=predicted_lead)).isoformat()
                    supabase.table("purchase_orders").insert({
                        "po_id": po_id,
                        "sku": sku,
                        "supplier_id": o.get("supplier_id") or sup.get("supplier_id"),
                        "quantity_ordered": int(o.get("quantity_ordered") or o.get("quantity") or 100),
                        "ordered_at": ordered_at,
                        "predicted_arrival": predicted_arrival,
                        "status": "pending",
                        "agent_reasoning": o.get("agent_reasoning", "Airia/auto-sim order"),
                        "stockout_days": 0,
                        "waste_units": 0,
                        "prediction_error": 0,
                    }).execute()
                    pending.append({
                        "po_id": po_id,
                        "sku": sku,
                        "quantity_ordered": int(o.get("quantity_ordered") or o.get("quantity") or 100),
                        "ordered_date": sim_dt.date(),
                        "due_date": sim_dt.date() + timedelta(days=actual_lead),
                        "predicted_lead_days": predicted_lead,
                        "stockout_days": 0,
                    })

            # 4) Increment stockout days for pending
            for po in pending:
                if products[po["sku"]]["current_stock"] <= 0:
                    po["stockout_days"] += 1

            # 5) Persist stock deltas for all SKUs
            for sku, prod in products.items():
                supabase.table("products").update({"current_stock": prod["current_stock"], "daily_velocity": prod.get("daily_velocity")}).eq("sku", sku).execute()

    print(f"Simulation complete. Pending POs left: {len(pending)}")


if __name__ == "__main__":
    random.seed(456)
    simulate()
