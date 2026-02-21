"""
simulate.py — StockPulse Data Simulator
Generates 6 months of realistic supermarket data with seasonal patterns
and pushes everything to Supabase.

Usage:
    pip install supabase python-dotenv
    python simulate.py
"""

import os
import random
import uuid
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Seed for reproducibility
random.seed(42)

# ─────────────────────────────────────────────
# REFERENCE DATA
# ─────────────────────────────────────────────

PRODUCTS = [
    {
        "sku": "SKU-001",
        "name": "Fresh Whole Milk",
        "category": "Dairy",
        "current_stock": 320,
        "reorder_point": 400,
        "safety_stock": 100,
        "unit_cost": 0.89,
        "shelf_life_days": 7,
        "daily_velocity": None,  # computed from sales
    },
    {
        "sku": "SKU-002",
        "name": "Heinz Baked Beans",
        "category": "Tinned",
        "current_stock": 890,
        "reorder_point": 200,
        "safety_stock": 80,
        "unit_cost": 0.65,
        "shelf_life_days": None,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-003",
        "name": "Paracetamol 500mg",
        "category": "Pharmacy",
        "current_stock": 85,
        "reorder_point": 150,
        "safety_stock": 60,
        "unit_cost": 2.49,
        "shelf_life_days": None,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-004",
        "name": "Pumpkin Soup",
        "category": "Seasonal",
        "current_stock": 45,
        "reorder_point": 100,
        "safety_stock": 40,
        "unit_cost": 1.20,
        "shelf_life_days": 730,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-005",
        "name": "Energy Drinks 250ml",
        "category": "Beverages",
        "current_stock": 180,
        "reorder_point": 250,
        "safety_stock": 100,
        "unit_cost": 1.10,
        "shelf_life_days": 365,
        "daily_velocity": None,
    },
]

SUPPLIERS = [
    {
        "supplier_id": "SUPPLIER-A",
        "name": "FreshFarm Dairy",
        "sku": "SKU-001",
        "predicted_lead_days": 7,
        "actual_lead_days": 8.2,   # accounts for December delays in history
        "reliability_score": 82,
        "notes": "Reliable most of year. Weather delays push lead time to 10-12 days in December.",
    },
    {
        "supplier_id": "SUPPLIER-B",
        "name": "NationalDist Ltd",
        "sku": "SKU-002",          # primary sku; also supplies 003/004/005
        "predicted_lead_days": 10,
        "actual_lead_days": 10.1,
        "reliability_score": 95,
        "notes": "Highly consistent. No seasonal variance observed.",
    },
]


# ─────────────────────────────────────────────
# DAILY SALES GENERATION
# ─────────────────────────────────────────────

def daily_units(sku: str, sale_date: date, days_ago: int) -> int:
    """Return simulated units sold for a SKU on a given date."""
    month = sale_date.month

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
            base = int(base * 2.0)   # flu season starts
        elif month == 11:
            base = int(base * 3.0)   # peak flu
        elif month == 12:
            base = int(base * 2.5)
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-004":  # Pumpkin Soup
        if month in (6, 7, 8):
            return random.randint(3, 7)   # near-zero off season
        elif month == 9:
            return random.randint(45, 75)   # ramping
        elif month == 10:
            return random.randint(130, 170)  # peak
        elif month == 11:
            return random.randint(100, 140)
        elif month == 12:
            return random.randint(30, 50)   # declining
        else:
            return random.randint(10, 20)

    elif sku == "SKU-005":  # Energy Drinks
        # Last 30 days = competitor stockout spike
        if days_ago <= 30:
            base = 140
        else:
            base = 60
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    return 0


def rolling_7day_avg(sales_series: list[int], idx: int) -> float:
    """Compute rolling 7-day average up to and including index idx."""
    window = sales_series[max(0, idx - 6): idx + 1]
    return round(sum(window) / len(window), 2)


# ─────────────────────────────────────────────
# BUILD SALES ROWS
# ─────────────────────────────────────────────

def build_sales_rows() -> tuple[list[dict], dict[str, float]]:
    """
    Returns:
        sales_rows  — list of dicts ready for Supabase insert
        velocities  — {sku: most_recent_7day_avg} for updating products
    """
    today = date.today()
    skus = [p["sku"] for p in PRODUCTS]
    all_rows = []
    velocities: dict[str, float] = {}

    for sku in skus:
        # Build 180 days oldest→newest
        days = list(range(179, -1, -1))  # 179 days ago → today
        units_series = []
        date_series = []

        for days_ago in reversed(days):
            sale_date = today - timedelta(days=days_ago)
            units = daily_units(sku, sale_date, days_ago)
            units_series.append(units)
            date_series.append(sale_date)

        # Build rows with rolling average
        for i, (sale_date, units) in enumerate(zip(date_series, units_series)):
            avg = rolling_7day_avg(units_series, i)
            all_rows.append(
                {
                    "sale_id": str(uuid.uuid4()),
                    "sku": sku,
                    "date": sale_date.isoformat(),
                    "units_sold": units,
                    "velocity_7day_avg": avg,
                }
            )

        # Most recent velocity
        velocities[sku] = rolling_7day_avg(units_series, len(units_series) - 1)

    return all_rows, velocities


# ─────────────────────────────────────────────
# HISTORICAL PURCHASE ORDERS
# ─────────────────────────────────────────────

def build_purchase_orders() -> list[dict]:
    """
    Six cycles of historical purchase orders demonstrating
    the agent learning over time. All are status=delivered
    except two recent pending ones.
    """
    today = date.today()

    def ts(days_ago: int) -> str:
        return (datetime.utcnow() - timedelta(days=days_ago)).isoformat()

    def arrival(days_ago: int, lead: int) -> str:
        return (today - timedelta(days=days_ago - lead)).isoformat()

    orders = []

    # ── CYCLE 1 — 5 months ago (~150 days) ───────────────────────────
    # Agent too optimistic on lead times; December delays not accounted for

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-001",
        "supplier_id": "SUPPLIER-A",
        "quantity_ordered": 1200,
        "ordered_at": ts(150),
        "predicted_arrival": arrival(150, 7),   # predicted 7 days
        "actual_arrival": arrival(150, 12),      # actually 12 days (December delay)
        "status": "delivered",
        "agent_reasoning": (
            "Stock at 280 units with daily sales of 200. "
            "Standard 7-day lead time assumed. "
            "December uplift not yet factored in — this was the agent's first winter cycle."
        ),
        "stockout_days": 3,
        "waste_units": 0,
        "prediction_error": -5,  # predicted 7, actual 12 → off by 5
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-003",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 180,
        "ordered_at": ts(148),
        "predicted_arrival": arrival(148, 10),
        "actual_arrival": arrival(148, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Paracetamol stock at 120 units. "
            "Base velocity 30 units/day. 10-day lead time from NationalDist. "
            "Flu season uplift not yet modelled."
        ),
        "stockout_days": 0,
        "waste_units": 5,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-002",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 500,
        "ordered_at": ts(146),
        "predicted_arrival": arrival(146, 10),
        "actual_arrival": arrival(146, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Baked Beans at 180 units, below reorder point of 200. "
            "Steady demand at 80 units/day. Ordering standard replenishment quantity."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    # ── CYCLE 2 — 4 months ago (~120 days) ───────────────────────────
    # Agent slightly improved — adjusted lead time but still underestimates

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-001",
        "supplier_id": "SUPPLIER-A",
        "quantity_ordered": 1400,
        "ordered_at": ts(120),
        "predicted_arrival": arrival(120, 9),   # updated estimate
        "actual_arrival": arrival(120, 11),
        "status": "delivered",
        "agent_reasoning": (
            "After the Cycle 1 delay, lead time estimate updated from 7 to 9 days. "
            "Milk velocity running at 240 units/day (November uplift). "
            "Ordered extra buffer to avoid repeat stockout."
        ),
        "stockout_days": 1,
        "waste_units": 0,
        "prediction_error": -2,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-004",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 600,
        "ordered_at": ts(118),
        "predicted_arrival": arrival(118, 10),
        "actual_arrival": arrival(118, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Pumpkin Soup entering peak October season. "
            "Stock at 60 units, velocity climbing to 140 units/day. "
            "Ordered 600 units to cover estimated 4-week peak demand."
        ),
        "stockout_days": 0,
        "waste_units": 12,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-005",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 350,
        "ordered_at": ts(116),
        "predicted_arrival": arrival(116, 10),
        "actual_arrival": arrival(116, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Energy Drinks at 190 units. Velocity steady at 62 units/day. "
            "Standard replenishment to maintain 3-week cover."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    # ── CYCLE 3 — 3 months ago (~90 days) ─────────────────────────────
    # Agent getting accurate — perfect lead time on milk

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-001",
        "supplier_id": "SUPPLIER-A",
        "quantity_ordered": 1600,
        "ordered_at": ts(90),
        "predicted_arrival": arrival(90, 11),
        "actual_arrival": arrival(90, 11),
        "status": "delivered",
        "agent_reasoning": (
            "Lead time revised to 11 days based on two consecutive December delays. "
            "Milk velocity at 265 units/day (December peak). "
            "Ordering 1600 units to cover 6-day demand plus 100-unit safety buffer."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-003",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 200,
        "ordered_at": ts(88),
        "predicted_arrival": arrival(88, 10),
        "actual_arrival": arrival(88, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Paracetamol at 95 units. Flu season active — velocity at 75 units/day. "
            "Ordered 200 units; velocity spike was larger than expected this cycle."
        ),
        "stockout_days": 2,
        "waste_units": 0,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-002",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 480,
        "ordered_at": ts(86),
        "predicted_arrival": arrival(86, 10),
        "actual_arrival": arrival(86, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Beans at 170 units — below reorder point. "
            "Velocity unchanged at 80 units/day. Routine replenishment."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    # ── CYCLE 4 — 2 months ago (~60 days) ─────────────────────────────
    # Flu season hits hard; agent underestimates Paracetamol demand

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-003",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 200,
        "ordered_at": ts(60),
        "predicted_arrival": arrival(60, 10),
        "actual_arrival": arrival(60, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Paracetamol stock critically low at 70 units. "
            "Flu season active — velocity estimated at 70 units/day. "
            "Ordered 200 units. NOTE: October flu pattern underestimated — "
            "actual demand ran at 90 units/day, causing 2-day stockout."
        ),
        "stockout_days": 2,
        "waste_units": 0,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-001",
        "supplier_id": "SUPPLIER-A",
        "quantity_ordered": 1500,
        "ordered_at": ts(58),
        "predicted_arrival": arrival(58, 11),
        "actual_arrival": arrival(58, 11),
        "status": "delivered",
        "agent_reasoning": (
            "Milk velocity stable at 200 units/day (post-December). "
            "11-day lead time confirmed accurate. Ordering normal replenishment."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-005",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 380,
        "ordered_at": ts(56),
        "predicted_arrival": arrival(56, 10),
        "actual_arrival": arrival(56, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Energy Drinks velocity ticking up slightly. Stock at 160 units. "
            "Ordering slightly above normal in case upward trend continues."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    # ── CYCLE 5 — 1 month ago (~30 days) ──────────────────────────────
    # Agent adds seasonal buffer for Paracetamol — slight overstock but no stockout

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-003",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 320,
        "ordered_at": ts(30),
        "predicted_arrival": arrival(30, 10),
        "actual_arrival": arrival(30, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Paracetamol at 80 units — below reorder point. "
            "Flu season peak: velocity at 90 units/day. "
            "Applied 30% seasonal buffer after Cycle 4 stockout. "
            "Ordered 320 units vs estimated need of 290 — small overstock acceptable."
        ),
        "stockout_days": 0,
        "waste_units": 30,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-002",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 500,
        "ordered_at": ts(28),
        "predicted_arrival": arrival(28, 10),
        "actual_arrival": arrival(28, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Baked Beans at 160 units. Velocity steady at 80/day. "
            "Standard replenishment to cover 6-week demand."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-005",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 500,
        "ordered_at": ts(26),
        "predicted_arrival": arrival(26, 10),
        "actual_arrival": arrival(26, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Energy Drinks velocity jumped to 140 units/day over last 2 weeks — "
            "possible competitor stockout detected. Increased order to 500 units "
            "to capitalise on demand surge and protect against further stock risk."
        ),
        "stockout_days": 0,
        "waste_units": 4,
        "prediction_error": 0,
    })

    # ── CYCLE 6 — 2 weeks ago (~14 days) — Agent nails it ─────────────
    # Near-perfect performance across all SKUs

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-001",
        "supplier_id": "SUPPLIER-A",
        "quantity_ordered": 1400,
        "ordered_at": ts(14),
        "predicted_arrival": arrival(14, 7),
        "actual_arrival": arrival(14, 7),
        "status": "delivered",
        "agent_reasoning": (
            "Milk stock at 320 units — below reorder point of 400. "
            "Post-December period: lead time reverts to standard 7 days (no weather risk). "
            "Velocity at 200 units/day. Ordering 1400 units for 7-day cover plus safety stock."
        ),
        "stockout_days": 0,
        "waste_units": 3,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-003",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 350,
        "ordered_at": ts(12),
        "predicted_arrival": arrival(12, 10),
        "actual_arrival": None,           # pending — for demo interest
        "status": "pending",
        "agent_reasoning": (
            "Paracetamol critically low at 85 units — only ~8 days of stock remaining. "
            "Flu season velocity confirmed at 90 units/day. 10-day lead time means we are "
            "already in risk window. Applying 30% seasonal buffer: ordering 350 units. "
            "This order MUST arrive before stockout on day 8."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-005",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 600,
        "ordered_at": ts(10),
        "predicted_arrival": arrival(10, 10),
        "actual_arrival": None,           # pending
        "status": "pending",
        "agent_reasoning": (
            "Energy Drinks velocity sustained at 140 units/day for 3 weeks — "
            "competitor stockout now confirmed as ongoing. Stock at 180 units "
            "gives only ~9 days cover against current demand. "
            "Ordering 600 units to maintain 30-day buffer at elevated velocity."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    return orders


# ─────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────

def clear_tables():
    """Delete existing data so simulate.py is safely re-runnable."""
    print("Clearing existing data...")
    # Order matters due to foreign key constraints
    supabase.table("purchase_orders").delete().neq("po_id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("sales").delete().neq("sale_id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("suppliers").delete().neq("supplier_id", "NONE").execute()
    supabase.table("products").delete().neq("sku", "NONE").execute()


def main():
    clear_tables()

    # ── 1. Build sales first so we can compute velocities ──
    print("Generating sales data...")
    sales_rows, velocities = build_sales_rows()

    # ── 2. Attach computed velocities to products ──
    for product in PRODUCTS:
        product["daily_velocity"] = round(velocities[product["sku"]], 2)

    # ── 3. Insert products ──
    supabase.table("products").insert(PRODUCTS).execute()
    print(f"Created {len(PRODUCTS)} products")

    # ── 4. Insert sales in batches (Supabase has a row limit per request) ──
    BATCH_SIZE = 200
    total_inserted = 0
    for i in range(0, len(sales_rows), BATCH_SIZE):
        batch = sales_rows[i: i + BATCH_SIZE]
        supabase.table("sales").insert(batch).execute()
        total_inserted += len(batch)

    print(f"Inserted {total_inserted} sales records (180 days x {len(PRODUCTS)} SKUs)")

    # ── 5. Insert suppliers ──
    supabase.table("suppliers").insert(SUPPLIERS).execute()
    print(f"Created {len(SUPPLIERS)} suppliers")

    # ── 6. Insert historical purchase orders ──
    orders = build_purchase_orders()
    supabase.table("purchase_orders").insert(orders).execute()
    print(f"Inserted {len(orders)} historical purchase orders across 6 cycles")

    print("\nSimulation complete. Database ready.")


if __name__ == "__main__":
    main()
