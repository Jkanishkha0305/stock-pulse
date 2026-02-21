"""
simulate_daily.py — rolling 30-day ops simulator

Continues from existing Supabase data and simulates day-by-day operations:
- Consumes stock using the same demand model as simulate.py
- Places purchase orders when stock drops below reorder_point
- Delivers orders after their (actual) lead time, updating stock and order status
- Writes daily sales rows so dashboards/Braintrust see fresh activity

Defaults: 30 simulated days ahead. Configure via SIM_DAYS env.
Run: uv run simulate_daily.py
"""

import os
import random
import uuid
from datetime import date, datetime, timedelta
from collections import defaultdict

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
SIM_DAYS = int(os.environ.get("SIM_DAYS", 30))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Reuse the demand patterns from simulate.py (kept in sync manually).
def daily_units(sku: str, sale_date: date, days_ago: int) -> int:
    month = sale_date.month
    weekday = sale_date.weekday()

    if sku == "SKU-001":  # Fresh Whole Milk
        base = 200
        if month == 11:
            base = int(base * 1.20)
        elif month == 12:
            base = int(base * 1.40)
        noise = random.uniform(-0.15, 0.15)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-002":  # Heinz Baked Beans
        base = 80
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-003":  # Paracetamol
        base = 30
        if month == 10:
            base = int(base * 2.0)
        elif month == 11:
            base = int(base * 3.0)
        elif month == 12:
            base = int(base * 2.5)
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-004":  # Pumpkin Soup
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

    elif sku == "SKU-005":  # Energy Drinks
        base = 140 if days_ago <= 30 else 60
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-006":  # Artisan Sourdough
        base = 120 if weekday < 5 else 90
        noise = random.uniform(-0.12, 0.12)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-007":  # Free-Range Eggs
        base = 110
        if month in (3, 4):
            base = int(base * 1.25)
        noise = random.uniform(-0.08, 0.08)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-008":  # Bananas
        base = 190
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-009":  # Chicken Breast
        base = 95
        if weekday in (4, 5):
            base = int(base * 1.20)
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-010":  # Sparkling Water
        base = 210
        if month in (6, 7, 8):
            base = int(base * 1.30)
        noise = random.uniform(-0.08, 0.08)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-011":  # Avocados
        base = 70
        if month == 1:
            base = int(base * 1.35)
        noise = random.uniform(-0.12, 0.12)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-012":  # Honey Granola
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
    # map sku -> supplier row (first match)
    mapping = {}
    for r in rows:
        mapping.setdefault(r["sku"], r)
    return mapping


def compute_velocity(history: list[int]) -> float:
    window = history[-7:]
    return round(sum(window) / len(window), 2) if window else 0.0


def simulate():
    products = load_products()
    suppliers = load_suppliers()
    demand_history: dict[str, list[int]] = defaultdict(list)

    # Track pending POs in-memory so we can deliver them later
    pending = []

    today = date.today()

    for day in range(1, SIM_DAYS + 1):
        sim_date = today + timedelta(days=day)
        print(f"Simulating day {day}/{SIM_DAYS} — {sim_date}")

        # 1) Consume demand & write sales
        sales_batch = []
        for sku, prod in products.items():
            demand = daily_units(sku, sim_date, days_ago=0)
            current = prod.get("current_stock", 0)
            sold = min(current, demand)
            prod["current_stock"] = max(0, current - sold)

            demand_history[sku].append(demand)
            velocity = compute_velocity(demand_history[sku])

            sales_batch.append({
                "sku": sku,
                "date": sim_date.isoformat(),
                "units_sold": sold,
                "velocity_7day_avg": velocity,
            })

        if sales_batch:
            supabase.table("sales").insert(sales_batch).execute()

        # 2) Deliver due pending POs
        delivered_po_ids = []
        for po in list(pending):
            if sim_date >= po["due_date"]:
                actual_lead = (sim_date - po["ordered_date"]).days
                prediction_error = po["predicted_lead_days"] - actual_lead

                supabase.table("purchase_orders").update({
                    "status": "delivered",
                    "actual_arrival": sim_date.isoformat(),
                    "prediction_error": prediction_error,
                    "stockout_days": po["stockout_days"],
                }).eq("po_id", po["po_id"]).execute()

                # add stock
                prod = products[po["sku"]]
                prod["current_stock"] += po["quantity_ordered"]

                delivered_po_ids.append(po["po_id"])
                pending.remove(po)

        # 3) Place new orders if below reorder point
        new_orders = []
        for sku, prod in products.items():
            if prod["current_stock"] < prod["reorder_point"]:
                supplier = suppliers.get(sku) or {}
                predicted_lead = int(round(supplier.get("predicted_lead_days", 7)))
                actual_lead = int(round(supplier.get("actual_lead_days", predicted_lead)))
                safety = prod.get("safety_stock", 0)
                # order enough to cover reorder_point + safety and a few days of demand
                est_daily = max(10, int(compute_velocity(demand_history[sku]) or prod.get("daily_velocity", 50)))
                quantity = max(prod["reorder_point"] + safety - prod["current_stock"], est_daily * predicted_lead)

                ordered_at = sim_date.isoformat()
                predicted_arrival = (sim_date + timedelta(days=predicted_lead)).isoformat()
                due_date = sim_date + timedelta(days=actual_lead)

                po_row = {
                    "po_id": str(uuid.uuid4()),
                    "sku": sku,
                    "supplier_id": supplier.get("supplier_id"),
                    "quantity_ordered": quantity,
                    "ordered_at": ordered_at,
                    "predicted_arrival": predicted_arrival,
                    "status": "pending",
                    "agent_reasoning": f"Auto-sim: stock {prod['current_stock']}, reorder_point {prod['reorder_point']}, ordering {quantity} units.",
                    "stockout_days": 0,
                    "waste_units": 0,
                    "prediction_error": 0,
                }
                # Insert and capture generated UUID
                inserted = supabase.table("purchase_orders").insert(po_row).execute().data[0]
                po_id = inserted.get("po_id")

                pending.append({
                    "po_id": po_id,
                    "sku": sku,
                    "quantity_ordered": quantity,
                    "ordered_date": sim_date,
                    "due_date": due_date,
                    "predicted_lead_days": predicted_lead,
                    "stockout_days": 0,
                })

        # 4) Track stockout days for pending orders
        for po in pending:
            if products[po["sku"]]["current_stock"] <= 0:
                po["stockout_days"] += 1

        # 5) Persist updated product stocks (update only, to avoid inserting null-required cols)
        for sku, prod in products.items():
            supabase.table("products").update({"current_stock": prod["current_stock"]}).eq("sku", sku).execute()

    print(f"Simulation complete. Pending POs left: {len(pending)}")


if __name__ == "__main__":
    random.seed(123)
    simulate()
