"""
simulate.py — StockPulse Data Simulator
Generates 2 years of realistic supermarket data with seasonal patterns
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

# Number of historical days to generate (2 years ≈ 730 days)
DAYS_BACK = 730

# Keep frontline stock levels realistic and non-zero so the demo and
# Braintrust evals always have interesting signals (no empty shelves at start).
STOCK_SCENARIO = {
    "SKU-001": 320,  # Milk — low-ish in December
    "SKU-002": 890,  # Beans — healthy buffer
    "SKU-003": 85,   # Paracetamol — critical
    "SKU-004": 45,   # Pumpkin Soup — season ending
    "SKU-005": 180,  # Energy Drinks — demand spike
    "SKU-006": 140,  # Sourdough — daily replenishment
    "SKU-007": 260,  # Eggs — staple
    "SKU-008": 380,  # Bananas — fast produce
    "SKU-009": 220,  # Chicken — fresh protein
    "SKU-010": 520,  # Sparkling Water — high volume
    "SKU-011": 160,  # Avocados — trending produce
    "SKU-012": 310,  # Granola — steady CPG
}

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
    {
        "sku": "SKU-006",
        "name": "Artisan Sourdough",
        "category": "Bakery",
        "current_stock": 140,
        "reorder_point": 160,
        "safety_stock": 60,
        "unit_cost": 1.40,
        "shelf_life_days": 3,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-007",
        "name": "Free-Range Eggs (12)",
        "category": "Dairy",
        "current_stock": 260,
        "reorder_point": 220,
        "safety_stock": 90,
        "unit_cost": 1.85,
        "shelf_life_days": 21,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-008",
        "name": "Bananas (kg)",
        "category": "Produce",
        "current_stock": 380,
        "reorder_point": 320,
        "safety_stock": 140,
        "unit_cost": 0.85,
        "shelf_life_days": 5,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-009",
        "name": "Chicken Breast (kg)",
        "category": "Meat",
        "current_stock": 220,
        "reorder_point": 200,
        "safety_stock": 80,
        "unit_cost": 4.10,
        "shelf_life_days": 7,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-010",
        "name": "Sparkling Water 500ml",
        "category": "Beverages",
        "current_stock": 520,
        "reorder_point": 420,
        "safety_stock": 160,
        "unit_cost": 0.42,
        "shelf_life_days": 365,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-011",
        "name": "Hass Avocados (4-pack)",
        "category": "Produce",
        "current_stock": 160,
        "reorder_point": 140,
        "safety_stock": 70,
        "unit_cost": 2.10,
        "shelf_life_days": 6,
        "daily_velocity": None,
    },
    {
        "sku": "SKU-012",
        "name": "Honey Granola 750g",
        "category": "Cereals",
        "current_stock": 310,
        "reorder_point": 260,
        "safety_stock": 110,
        "unit_cost": 2.80,
        "shelf_life_days": 540,
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
        "sku": "SKU-002",          # primary sku; also supplies 003/004/005/010/012
        "predicted_lead_days": 10,
        "actual_lead_days": 10.1,
        "reliability_score": 95,
        "notes": "Highly consistent. No seasonal variance observed.",
    },
    {
        "supplier_id": "SUPPLIER-C",
        "name": "FreshFields Produce",
        "sku": "SKU-008",          # bananas, avocados
        "predicted_lead_days": 4,
        "actual_lead_days": 4.3,
        "reliability_score": 90,
        "notes": "Produce freshness focused; minor weather variability.",
    },
    {
        "supplier_id": "SUPPLIER-D",
        "name": "MeadowMeat",
        "sku": "SKU-009",
        "predicted_lead_days": 6,
        "actual_lead_days": 6.2,
        "reliability_score": 88,
        "notes": "Chilled chain; minor Friday delays.",
    },
    {
        "supplier_id": "SUPPLIER-E",
        "name": "BakeHouse Collective",
        "sku": "SKU-006",
        "predicted_lead_days": 2,
        "actual_lead_days": 2.4,
        "reliability_score": 86,
        "notes": "Fresh daily bakery runs; weekends slower.",
    },
    {
        "supplier_id": "SUPPLIER-F",
        "name": "Staple Farms",
        "sku": "SKU-007",
        "predicted_lead_days": 5,
        "actual_lead_days": 5.1,
        "reliability_score": 92,
        "notes": "Eggs supply stable; slight Easter uplift.",
    },
]


# ─────────────────────────────────────────────
# DAILY SALES GENERATION
# ─────────────────────────────────────────────

def daily_units(sku: str, sale_date: date, days_ago: int) -> int:
    """Return simulated units sold for a SKU on a given date."""
    month = sale_date.month
    weekday = sale_date.weekday()  # 0 = Mon

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

    elif sku == "SKU-006":  # Artisan Sourdough
        base = 120 if weekday < 5 else 90  # slightly lower on weekends
        noise = random.uniform(-0.12, 0.12)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-007":  # Free-Range Eggs
        base = 110
        # Easter uplift (~April)
        if month == 3 or month == 4:
            base = int(base * 1.25)
        noise = random.uniform(-0.08, 0.08)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-008":  # Bananas
        base = 190
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-009":  # Chicken Breast
        base = 95
        if weekday in (4, 5):  # Fri/Sat barbecue bump
            base = int(base * 1.20)
        noise = random.uniform(-0.10, 0.10)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-010":  # Sparkling Water
        base = 210
        # Summer uplift June-August
        if month in (6, 7, 8):
            base = int(base * 1.30)
        noise = random.uniform(-0.08, 0.08)
        return max(1, int(base * (1 + noise)))

    elif sku == "SKU-011":  # Avocados
        base = 70
        # January healthy eating spike
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
        # Build N days oldest→newest
        days = list(range(DAYS_BACK - 1, -1, -1))  # e.g., 729 days ago → today
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

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-006",
        "supplier_id": "SUPPLIER-E",
        "quantity_ordered": 260,
        "ordered_at": ts(24),
        "predicted_arrival": arrival(24, 2),
        "actual_arrival": arrival(24, 2),
        "status": "delivered",
        "agent_reasoning": (
            "Sourdough runs low ahead of weekend. Velocity 120/day weekdays, 90/day weekends. "
            "Two-day lead time, ordered 260 to cover next two days plus buffer."
        ),
        "stockout_days": 0,
        "waste_units": 6,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-007",
        "supplier_id": "SUPPLIER-F",
        "quantity_ordered": 400,
        "ordered_at": ts(22),
        "predicted_arrival": arrival(22, 5),
        "actual_arrival": arrival(22, 5),
        "status": "delivered",
        "agent_reasoning": (
            "Eggs velocity stable at 110/day. Easter uplift tapering. "
            "Ordered 400 units to maintain 4-day cover plus safety stock."
        ),
        "stockout_days": 0,
        "waste_units": 12,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-010",
        "supplier_id": "SUPPLIER-B",
        "quantity_ordered": 900,
        "ordered_at": ts(21),
        "predicted_arrival": arrival(21, 10),
        "actual_arrival": arrival(21, 10),
        "status": "delivered",
        "agent_reasoning": (
            "Sparkling Water demand rising into summer. Velocity 210/day. "
            "Ordering 900 units to cover 4 days plus warehouse buffer."
        ),
        "stockout_days": 0,
        "waste_units": 0,
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

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-009",
        "supplier_id": "SUPPLIER-D",
        "quantity_ordered": 280,
        "ordered_at": ts(13),
        "predicted_arrival": arrival(13, 6),
        "actual_arrival": arrival(13, 6),
        "status": "delivered",
        "agent_reasoning": (
            "Chicken breast at 220 units, velocity 100/day with weekend bumps. "
            "Lead time 6 days. Ordering 280 to cover 3 days plus safety stock."
        ),
        "stockout_days": 0,
        "waste_units": 5,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-008",
        "supplier_id": "SUPPLIER-C",
        "quantity_ordered": 500,
        "ordered_at": ts(11),
        "predicted_arrival": arrival(11, 4),
        "actual_arrival": None,           # pending
        "status": "pending",
        "agent_reasoning": (
            "Bananas moving at 190/day. FreshFields lead time 4 days. "
            "Ordering 500 to maintain 2.5 days cover with ripeness buffer."
        ),
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    })

    orders.append({
        "po_id": str(uuid.uuid4()),
        "sku": "SKU-011",
        "supplier_id": "SUPPLIER-C",
        "quantity_ordered": 260,
        "ordered_at": ts(9),
        "predicted_arrival": arrival(9, 4),
        "actual_arrival": arrival(9, 4),
        "status": "delivered",
        "agent_reasoning": (
            "Avocado velocity 70/day; January spike subsided but still elevated. "
            "Ordering 260 for 3+ days cover; managing ripeness stages to avoid waste."
        ),
        "stockout_days": 0,
        "waste_units": 8,
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

    # ── 2. Attach computed velocities to products and pin realistic stock levels ──
    for product in PRODUCTS:
        product["daily_velocity"] = round(velocities[product["sku"]], 2)
        # Ensure current_stock is set to the scenario values (never zero)
        # so dashboards + evals see meaningful, non-empty shelves.
        product["current_stock"] = STOCK_SCENARIO.get(product["sku"], product["current_stock"])

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

    print(f"Inserted {total_inserted} sales records ({DAYS_BACK} days x {len(PRODUCTS)} SKUs)")

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
