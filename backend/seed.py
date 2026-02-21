"""
Seed Supabase with 6 months of realistic supermarket simulation data.
Run: python seed.py
Requires SUPABASE_URL and SUPABASE_KEY in .env
"""
import os
import random
import uuid
from datetime import date, datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
sb = create_client(url, key)

random.seed(42)  # reproducible

# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
PRODUCTS = [
    {"sku": "SKU-001", "name": "Fresh Whole Milk",   "category": "Dairy",     "current_stock": 420, "reorder_point": 300, "safety_stock": 150, "unit_cost": 0.85,  "shelf_life_days": 7},
    {"sku": "SKU-002", "name": "Heinz Baked Beans",  "category": "Grocery",   "current_stock": 240, "reorder_point": 200, "safety_stock": 80,  "unit_cost": 1.20,  "shelf_life_days": 365},
    {"sku": "SKU-003", "name": "Paracetamol 500mg",  "category": "Pharmacy",  "current_stock": 85,  "reorder_point": 100, "safety_stock": 50,  "unit_cost": 0.35,  "shelf_life_days": 730},
    {"sku": "SKU-004", "name": "Pumpkin Soup",        "category": "Grocery",   "current_stock": 45,  "reorder_point": 80,  "safety_stock": 40,  "unit_cost": 2.10,  "shelf_life_days": 365},
    {"sku": "SKU-005", "name": "Energy Drinks",       "category": "Beverages", "current_stock": 280, "reorder_point": 200, "safety_stock": 60,  "unit_cost": 1.50,  "shelf_life_days": 180},
]

# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------
SUPPLIERS = [
    {"supplier_id": "SUP-A", "name": "Supplier A (Dairy)",    "sku": "SKU-001", "predicted_lead_days": 7,  "actual_lead_days": 7,  "reliability_score": 85, "notes": "Dairy specialist. +3 days in December."},
    {"supplier_id": "SUP-B", "name": "Supplier B (National)", "sku": None,      "predicted_lead_days": 10, "actual_lead_days": 10, "reliability_score": 92, "notes": "Reliable national distributor."},
    {"supplier_id": "SUP-C", "name": "Supplier C (Wholesale)","sku": None,      "predicted_lead_days": 7,  "actual_lead_days": 8,  "reliability_score": 78, "notes": "Cheapest prices. Occasionally slow."},
]

# ---------------------------------------------------------------------------
# Sales simulation helpers
# ---------------------------------------------------------------------------
def daily_units(sku: str, d: date) -> int:
    m = d.month
    if sku == "SKU-001":  # Milk: base 200, Christmas spike
        base = 200
        if m == 12:
            base = 320
        elif m in (1, 2):
            base = 220
        return max(0, int(base + random.gauss(0, 15)))

    if sku == "SKU-002":  # Beans: steady 80 ±10%
        return max(0, int(80 + random.gauss(0, 8)))

    if sku == "SKU-003":  # Paracetamol: flu season spike Oct-Feb
        base = 30
        if m in (10, 11, 12, 1, 2):
            base = 90
        return max(0, int(base + random.gauss(0, 5)))

    if sku == "SKU-004":  # Pumpkin Soup: autumn only
        if m in (10, 11):
            base = 150
        elif m == 9:
            base = 40
        elif m == 12:
            base = 20
        else:
            base = 0
        return max(0, int(base + random.gauss(0, 10)))

    if sku == "SKU-005":  # Energy Drinks: competitor stockout spike in Jan-Feb 2026
        base = 60
        if d >= date(2026, 1, 1):
            base = 140  # competitor ran out
        elif m in (6, 7, 8):
            base = 80   # summer bump
        return max(0, int(base + random.gauss(0, 12)))

    return 0


def rolling_7day_avg(history: list[int]) -> float:
    window = history[-7:] if len(history) >= 7 else history
    return round(sum(window) / len(window), 2) if window else 0.0


# ---------------------------------------------------------------------------
# Agent cycle simulation (6 cycles — improving accuracy)
# ---------------------------------------------------------------------------
CYCLE_ACCURACIES = [55, 58, 63, 71, 82, 88]

CYCLE_PO_TEMPLATES = [
    # Cycle 1-2: agent uses wrong lead times, some late orders
    [("SKU-001", "SUP-A", 1200, "Reorder triggered (stock below threshold). Lead time estimated 7d."),
     ("SKU-003", "SUP-B", 200,  "Paracetamol restocked. Flu season not yet detected.")],
    [("SKU-004", "SUP-B", 300,  "Pumpkin Soup: seasonal demand not yet learned. Slight over-order."),
     ("SKU-002", "SUP-C", 500,  "Beans restocked via SUP-C for cost savings.")],
    # Cycle 3-4: agent starts correcting
    [("SKU-001", "SUP-A", 1400, "Milk: Christmas spike detected. Increased order quantity by 15%."),
     ("SKU-003", "SUP-B", 400,  "Paracetamol: flu season identified. Tripling normal order.")],
    [("SKU-005", "SUP-C", 800,  "Energy Drinks: velocity anomaly detected (+80%). Ordering buffer stock."),
     ("SKU-004", "SUP-B", 200,  "Pumpkin Soup: autumn season confirmed. Smart reorder.")],
    # Cycle 5-6: agent predicts accurately
    [("SKU-001", "SUP-A", 1500, "Milk: pre-Christmas stock secured. Predicted spike 3 weeks early."),
     ("SKU-003", "SUP-A", 600,  "Paracetamol: flu season pre-loaded. Zero stockout projected.")],
    [("SKU-005", "SUP-C", 1000, "Energy Drinks: competitor stockout confirmed. Capitalising on demand surge."),
     ("SKU-002", "SUP-B", 600,  "Beans: seasonal demand bump for winter comfort food. Ordering ahead.")],
]

# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
def seed_products():
    print("Seeding products...")
    for p in PRODUCTS:
        sb.table("products").upsert(p).execute()
    print(f"  {len(PRODUCTS)} products inserted.")


def seed_suppliers():
    print("Seeding suppliers...")
    for s in SUPPLIERS:
        sb.table("suppliers").upsert(s).execute()
    print(f"  {len(SUPPLIERS)} suppliers inserted.")


def seed_sales():
    print("Seeding sales (6 months of daily data)...")
    start = date(2025, 8, 1)
    end = date(2026, 2, 21)  # today

    batch: list[dict] = []
    history: dict[str, list[int]] = {p["sku"]: [] for p in PRODUCTS}
    d = start
    while d <= end:
        for p in PRODUCTS:
            sku = p["sku"]
            units = daily_units(sku, d)
            history[sku].append(units)
            vel = rolling_7day_avg(history[sku])
            batch.append({
                "sale_id": f"{sku}-{d.isoformat()}",
                "sku": sku,
                "date": d.isoformat(),
                "units_sold": units,
                "velocity_7day_avg": vel,
            })
        d += timedelta(days=1)

    # Insert in chunks of 500
    for i in range(0, len(batch), 500):
        sb.table("sales").upsert(batch[i:i+500]).execute()
        print(f"  Inserted sales rows {i} – {min(i+500, len(batch))}")
    print(f"  {len(batch)} total sale rows seeded.")


def seed_purchase_orders_and_cycles():
    print("Seeding agent cycles and purchase orders...")
    # Spread 6 cycles over the past 6 months
    cycle_start_dates = [
        date(2025, 8, 15),
        date(2025, 9, 20),
        date(2025, 10, 25),
        date(2025, 11, 28),
        date(2025, 12, 20),
        date(2026, 1, 30),
    ]
    all_suppliers = {s["supplier_id"]: s for s in SUPPLIERS}

    for i, (cycle_date, pos, accuracy) in enumerate(
        zip(cycle_start_dates, CYCLE_PO_TEMPLATES, CYCLE_ACCURACIES)
    ):
        cycle_index = i + 1
        timestamp = datetime.combine(cycle_date, datetime.min.time()).isoformat() + "Z"

        # Insert agent cycle
        sb.table("agent_cycles").upsert({
            "cycle_index": cycle_index,
            "accuracy": accuracy,
            "timestamp": timestamp,
            "orders_placed": len(pos),
        }).execute()

        # Insert POs for this cycle
        for sku, supplier_id, qty, reasoning in pos:
            product = next(p for p in PRODUCTS if p["sku"] == sku)
            supplier = all_suppliers[supplier_id]
            lead_days = supplier["predicted_lead_days"]
            # Early cycles have larger prediction errors
            actual_extra = random.choice([0, 1, 2, 3]) if cycle_index <= 2 else random.choice([0, 0, 1])
            predicted_arrival = (cycle_date + timedelta(days=lead_days)).isoformat()
            actual_arrival = (cycle_date + timedelta(days=lead_days + actual_extra)).isoformat()

            po = {
                "po_id": f"PO-C{cycle_index}-{sku}",
                "sku": sku,
                "supplier_id": supplier_id,
                "quantity_ordered": qty,
                "ordered_at": timestamp,
                "predicted_arrival": predicted_arrival,
                "actual_arrival": actual_arrival,
                "status": "delivered",
                "agent_reasoning": reasoning,
                "prediction_error": actual_extra,
            }
            sb.table("purchase_orders").upsert(po).execute()

    print(f"  6 cycles and {sum(len(p) for p in CYCLE_PO_TEMPLATES)} purchase orders seeded.")


if __name__ == "__main__":
    print("=" * 50)
    print("StockPulse — Supabase Seeder")
    print("=" * 50)
    seed_products()
    seed_suppliers()
    seed_sales()
    seed_purchase_orders_and_cycles()
    print("=" * 50)
    print("Done! Your Supabase database is ready.")
    print("=" * 50)
