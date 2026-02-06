"""
Supabase client and query helpers.
Falls back to in-memory demo data if SUPABASE_URL is not configured.
"""
import os
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Supabase client (lazy init)
# ---------------------------------------------------------------------------
_supabase = None


def _client():
    global _supabase
    if _supabase is not None:
        return _supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if url and key:
        from supabase import create_client
        _supabase = create_client(url, key)
    return _supabase


def _use_supabase() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))


# ---------------------------------------------------------------------------
# Demo / fallback data (used when Supabase is not configured)
# ---------------------------------------------------------------------------
DEMO_PRODUCTS = [
    {"sku": "SKU-001", "name": "Fresh Whole Milk", "category": "Dairy", "current_stock": 420, "reorder_point": 300, "safety_stock": 150, "unit_cost": 0.85, "shelf_life_days": 7},
    {"sku": "SKU-002", "name": "Heinz Baked Beans", "category": "Grocery", "current_stock": 240, "reorder_point": 200, "safety_stock": 80, "unit_cost": 1.20, "shelf_life_days": 365},
    {"sku": "SKU-003", "name": "Paracetamol 500mg", "category": "Pharmacy", "current_stock": 85, "reorder_point": 100, "safety_stock": 50, "unit_cost": 0.35, "shelf_life_days": 730},
    {"sku": "SKU-004", "name": "Pumpkin Soup", "category": "Grocery", "current_stock": 45, "reorder_point": 80, "safety_stock": 40, "unit_cost": 2.10, "shelf_life_days": 365},
    {"sku": "SKU-005", "name": "Energy Drinks", "category": "Beverages", "current_stock": 280, "reorder_point": 200, "safety_stock": 60, "unit_cost": 1.50, "shelf_life_days": 180},
]

DEMO_SALES_VELOCITY = {
    "SKU-001": 30.0,
    "SKU-002": 12.0,
    "SKU-003": 8.0,
    "SKU-004": 15.0,
    "SKU-005": 25.0,
}

DEMO_SUPPLIERS = [
    {"supplier_id": "SUP-A", "name": "Supplier A (Dairy)", "sku": "SKU-001", "predicted_lead_days": 7, "actual_lead_days": 7, "reliability_score": 85, "notes": "+3 days in December"},
    {"supplier_id": "SUP-B", "name": "Supplier B (National)", "sku": None, "predicted_lead_days": 10, "actual_lead_days": 10, "reliability_score": 92, "notes": "Consistent"},
    {"supplier_id": "SUP-C", "name": "Supplier C (Wholesale)", "sku": None, "predicted_lead_days": 7, "actual_lead_days": 8, "reliability_score": 78, "notes": "Price competitive"},
]

# In-memory fallback state
_purchase_orders: list[dict[str, Any]] = []
_agent_cycles: list[dict[str, Any]] = []
_cycle_counter = 6


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
def get_products() -> list[dict[str, Any]]:
    if _use_supabase():
        try:
            result = _client().table("products").select("*").execute()
            return result.data or []
        except Exception as e:
            print(f"[DB] get_products error: {e}")
    return [p.copy() for p in DEMO_PRODUCTS]


def update_product_stock(sku: str, new_stock: int) -> None:
    if _use_supabase():
        try:
            _client().table("products").update({"current_stock": new_stock}).eq("sku", sku).execute()
            return
        except Exception as e:
            print(f"[DB] update_product_stock error: {e}")
    for p in DEMO_PRODUCTS:
        if p["sku"] == sku:
            p["current_stock"] = new_stock
            break


# ---------------------------------------------------------------------------
# Sales velocity
# ---------------------------------------------------------------------------
def get_sales_velocity_by_sku() -> dict[str, float]:
    """Current daily velocity per SKU. Uses daily_velocity column from products table."""
    if _use_supabase():
        try:
            result = _client().table("products").select("sku,daily_velocity").execute()
            return {
                row["sku"]: float(row["daily_velocity"] or 0)
                for row in (result.data or [])
                if row.get("daily_velocity") is not None
            }
        except Exception as e:
            print(f"[DB] get_sales_velocity_by_sku error: {e}")
    return dict(DEMO_SALES_VELOCITY)


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------
def get_suppliers() -> list[dict[str, Any]]:
    if _use_supabase():
        try:
            result = _client().table("suppliers").select("*").execute()
            return result.data or []
        except Exception as e:
            print(f"[DB] get_suppliers error: {e}")
    return [s.copy() for s in DEMO_SUPPLIERS]


def update_supplier_reliability(supplier_id: str, actual_lead_days: int, reliability_score: float) -> None:
    if _use_supabase():
        try:
            _client().table("suppliers").update({
                "actual_lead_days": actual_lead_days,
                "reliability_score": round(reliability_score, 1),
            }).eq("supplier_id", supplier_id).execute()
        except Exception as e:
            print(f"[DB] update_supplier_reliability error: {e}")


# ---------------------------------------------------------------------------
# Purchase orders
# ---------------------------------------------------------------------------
def get_recent_purchase_orders(limit: int = 20) -> list[dict[str, Any]]:
    if _use_supabase():
        try:
            result = (
                _client()
                .table("purchase_orders")
                .select("*")
                .order("ordered_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[DB] get_recent_purchase_orders error: {e}")
    return sorted(_purchase_orders, key=lambda x: x.get("ordered_at", ""), reverse=True)[:limit]


def insert_purchase_order(po: dict[str, Any]) -> None:
    if _use_supabase():
        try:
            _client().table("purchase_orders").insert(po).execute()
            return
        except Exception as e:
            print(f"[DB] insert_purchase_order error: {e}")
    _purchase_orders.append(po)


# ---------------------------------------------------------------------------
# Agent cycles
# ---------------------------------------------------------------------------
def get_agent_cycles(limit: int = 10) -> list[dict[str, Any]]:
    if _use_supabase():
        try:
            result = (
                _client()
                .table("agent_cycles")
                .select("*")
                .order("cycle_index", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            print(f"[DB] get_agent_cycles error: {e}")
    return sorted(_agent_cycles, key=lambda x: x.get("cycle_index", 0), reverse=True)[:limit]


def get_cycle_count() -> int:
    if _use_supabase():
        try:
            result = (
                _client()
                .table("agent_cycles")
                .select("cycle_index")
                .order("cycle_index", desc=True)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            if rows:
                return rows[0].get("cycle_index", 0)
            return 0
        except Exception as e:
            print(f"[DB] get_cycle_count error: {e}")
    global _cycle_counter
    return _cycle_counter


def insert_agent_cycle(cycle: dict[str, Any]) -> None:
    global _cycle_counter
    if _use_supabase():
        try:
            _client().table("agent_cycles").insert(cycle).execute()
            _cycle_counter = cycle.get("cycle_index", _cycle_counter)
            return
        except Exception as e:
            print(f"[DB] insert_agent_cycle error: {e}")
    _agent_cycles.append(cycle)
    _cycle_counter = cycle.get("cycle_index", _cycle_counter)


# ---------------------------------------------------------------------------
# Composite helpers
# ---------------------------------------------------------------------------
def get_products_with_velocity() -> list[dict[str, Any]]:
    products = get_products()
    velocity = get_sales_velocity_by_sku()
    for p in products:
        p["velocity_7day_avg"] = velocity.get(p["sku"], 0.0)
    return products
