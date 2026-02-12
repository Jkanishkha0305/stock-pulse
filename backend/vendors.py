"""
Simulated vendors: 2-3 mock vendors return offers (price, lead_days).
Conversation generator turns offers into chat-style messages for the UI.
"""
import random
from typing import Any

# Three vendors: two match real Supabase supplier IDs; third is a simulated competitor bid
VENDORS = [
    {"vendor_id": "SUPPLIER-A", "name": "FreshFarm Dairy",    "persona": "price",    "base_lead_days": 7,  "base_price_mult": 0.95},
    {"vendor_id": "SUPPLIER-B", "name": "NationalDist Ltd",   "persona": "speed",    "base_lead_days": 10, "base_price_mult": 1.05},
    {"vendor_id": "SUPPLIER-C", "name": "BulkBuy Wholesale",  "persona": "balanced", "base_lead_days": 8,  "base_price_mult": 1.0},
]


def get_offer(vendor_id: str, sku: str, quantity: int, unit_cost: float) -> dict[str, Any]:
    """
    Simulated offer from a vendor. Returns price_per_unit, lead_days, total, terms.
    """
    vendor = next((v for v in VENDORS if v["vendor_id"] == vendor_id), None)
    if not vendor:
        return {"vendor_id": vendor_id, "error": "Unknown vendor"}
    # Add slight randomness for demo
    lead = vendor["base_lead_days"] + random.randint(-1, 2)
    lead = max(3, min(14, lead))
    mult = vendor["base_price_mult"] * (0.98 + random.random() * 0.06)
    price_per_unit = round(unit_cost * mult, 2)
    total = round(price_per_unit * quantity, 2)
    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor["name"],
        "sku": sku,
        "quantity": quantity,
        "price_per_unit": price_per_unit,
        "total_gbp": total,
        "lead_days": lead,
        "terms": "Net 30" if vendor["persona"] == "price" else "Net 14",
    }


def get_all_offers(sku: str, quantity: int, unit_cost: float) -> list[dict[str, Any]]:
    """Get offers from all 3 simulated vendors."""
    return [get_offer(v["vendor_id"], sku, quantity, unit_cost) for v in VENDORS]


def pick_best_offer(offers: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Choose best offer by simple score: lower total + lower lead_days wins.
    Normalize and sum inverse rank.
    """
    valid = [o for o in offers if "error" not in o]
    if not valid:
        return None
    totals = [o["total_gbp"] for o in valid]
    leads = [o["lead_days"] for o in valid]
    max_total, min_total = max(totals), min(totals)
    max_lead, min_lead = max(leads), min(leads)
    def norm_total(t): return (t - min_total) / (max_total - min_total + 1e-6)
    def norm_lead(l): return (l - min_lead) / (max_lead - min_lead + 1e-6)
    scored = []
    for o in valid:
        s = 0.5 * (1 - norm_total(o["total_gbp"])) + 0.5 * (1 - norm_lead(o["lead_days"]))
        scored.append((s, o))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def generate_conversation(vendor_name: str, offer: dict[str, Any], sku_name: str) -> list[dict[str, str]]:
    """
    Generate 2-4 chat-style messages (agent message, vendor reply) for the UI.
    """
    q = offer.get("quantity", 0)
    lead = offer.get("lead_days", 0)
    total = offer.get("total_gbp", 0)
    messages = [
        {"role": "agent", "text": f"We need {q} units of {sku_name} with delivery as soon as possible. Can you quote?"},
        {"role": "vendor", "text": f"We can deliver in {lead} days. Total would be £{total:.2f} (Net 30 payment)."},
        {"role": "agent", "text": "Can you confirm lead time and total?"},
        {"role": "vendor", "text": f"Confirmed: {lead} days, £{total:.2f} total."},
    ]
    return messages


def run_negotiation(sku: str, sku_name: str, quantity: int, unit_cost: float) -> dict[str, Any]:
    """
    Run full simulated negotiation: get 3 offers, generate conversations, pick best.
    Returns chosen offer + all vendor conversations for the UI.
    """
    offers = get_all_offers(sku, quantity, unit_cost)
    chosen = pick_best_offer(offers)
    conversations = []
    for o in offers:
        if "error" in o:
            continue
        conv = generate_conversation(o["vendor_name"], o, sku_name)
        conversations.append({
            "vendor_id": o["vendor_id"],
            "vendor_name": o["vendor_name"],
            "offer": o,
            "messages": conv,
            "chosen": chosen and o["vendor_id"] == chosen["vendor_id"],
        })
    return {
        "sku": sku,
        "sku_name": sku_name,
        "quantity": quantity,
        "offers": offers,
        "chosen_offer": chosen,
        "conversations": conversations,
    }
