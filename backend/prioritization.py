"""
Prioritize SKUs by urgency: what's low first.
Computes days_remaining and urgency score; returns top N for the agent.
"""
from typing import Any


def days_of_stock_remaining(current_stock: float, velocity_7day_avg: float) -> float | None:
    """Days until stock runs out at current velocity. None if velocity <= 0."""
    if not velocity_7day_avg or velocity_7day_avg <= 0:
        return None
    return current_stock / velocity_7day_avg


def urgency_score(
    current_stock: float,
    reorder_point: float,
    safety_stock: float,
    velocity_7day_avg: float,
    safety_buffer_days: float = 3.0,
) -> float:
    """
    Higher = more urgent. Based on days remaining vs reorder logic.
    Uses (reorder_point - current_stock) and velocity so we act on "low first".
    """
    if velocity_7day_avg <= 0:
        return 0.0
    days_left = current_stock / velocity_7day_avg
    # Urgent if below reorder point or days_left is small
    stock_deficit = max(0, reorder_point - current_stock)
    # Score: deficit weight + inverse of days left (fewer days = more urgent)
    deficit_score = min(1.0, stock_deficit / max(1, reorder_point))
    days_score = max(0, 1.0 - (days_left / 30.0))  # 30 days left = 0, 0 days = 1
    return 0.6 * deficit_score + 0.4 * days_score


def prioritize_low_stock(
    products_with_velocity: list[dict[str, Any]],
    top_n: int = 5,
    safety_buffer_days: float = 3.0,
) -> list[dict[str, Any]]:
    """
    Rank products by urgency (low stock first) and return top N with
    days_remaining and urgency_score attached.
    """
    enriched = []
    for p in products_with_velocity:
        vel = p.get("velocity_7day_avg") or 0.0
        days_rem = days_of_stock_remaining(float(p.get("current_stock", 0)), vel)
        score = urgency_score(
            float(p.get("current_stock", 0)),
            float(p.get("reorder_point", 0)),
            float(p.get("safety_stock", 0)),
            vel,
            safety_buffer_days,
        )
        enriched.append({
            **p,
            "days_remaining": days_rem,
            "urgency_score": round(score, 4),
        })
    # Sort by urgency descending (most urgent first)
    enriched.sort(key=lambda x: x["urgency_score"], reverse=True)
    return enriched[:top_n]
