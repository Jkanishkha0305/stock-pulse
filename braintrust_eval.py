"""
braintrust_eval.py — StockPulse Evaluation Runner
Reads historical purchase orders from Supabase, scores each cycle,
and pushes results to Braintrust to prove self-improvement over time.

Usage:
    pip install supabase braintrust python-dotenv
    python braintrust_eval.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import braintrust
from braintrust import Eval

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BRAINTRUST_API_KEY = os.environ["BRAINTRUST_API_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

PROJECT_NAME = "stockpulse-evals"

# ─────────────────────────────────────────────
# CYCLE ASSIGNMENT
# Cycles are inferred from ordered_at timestamp.
# Approx boundaries (days ago):
#   Cycle 1: 140–160 days ago  (5 months)
#   Cycle 2: 110–130 days ago  (4 months)
#   Cycle 3: 80–100 days ago   (3 months)
#   Cycle 4: 50–70 days ago    (2 months)
#   Cycle 5: 20–40 days ago    (1 month)
#   Cycle 6: 0–20 days ago     (2 weeks)
# ─────────────────────────────────────────────

from datetime import datetime, timezone

def assign_cycle(ordered_at_str: str) -> int:
    """Map an order's timestamp to a cycle number 1-6."""
    ordered_at = datetime.fromisoformat(ordered_at_str.replace("Z", "+00:00"))
    if ordered_at.tzinfo is None:
        ordered_at = ordered_at.replace(tzinfo=timezone.utc)

    now = datetime.now(tz=timezone.utc)
    days_ago = (now - ordered_at).days

    if days_ago >= 140:
        return 1
    elif days_ago >= 110:
        return 2
    elif days_ago >= 80:
        return 3
    elif days_ago >= 50:
        return 4
    elif days_ago >= 20:
        return 5
    else:
        return 6


# ─────────────────────────────────────────────
# FETCH DATA FROM SUPABASE
# ─────────────────────────────────────────────

def load_orders() -> list[dict]:
    """
    Pull all delivered purchase orders and enrich each with:
    - cycle number
    - velocity_at_time (from matching sales record)
    - seasonal_flag (True if flu/Christmas season)
    """
    response = (
        supabase.table("purchase_orders")
        .select("*")
        .eq("status", "delivered")
        .execute()
    )
    orders = response.data
    print(f"Loaded {len(orders)} purchase orders from Supabase")
    return orders


def get_velocity_at_time(sku: str, ordered_at_str: str) -> float:
    """Fetch the closest velocity_7day_avg from the sales table."""
    order_date = ordered_at_str[:10]  # YYYY-MM-DD
    response = (
        supabase.table("sales")
        .select("velocity_7day_avg, date")
        .eq("sku", sku)
        .lte("date", order_date)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return float(response.data[0]["velocity_7day_avg"])
    return 0.0


def is_seasonal(sku: str, ordered_at_str: str) -> bool:
    """Flag orders placed during known seasonal demand spikes."""
    month = int(ordered_at_str[5:7])
    if sku == "SKU-003" and month in (10, 11, 12):  # flu season
        return True
    if sku == "SKU-001" and month in (11, 12):       # Christmas milk spike
        return True
    if sku == "SKU-004" and month in (9, 10, 11):    # pumpkin soup season
        return True
    return False


# ─────────────────────────────────────────────
# SCORING FUNCTIONS
# ─────────────────────────────────────────────

def lead_time_accuracy(output: dict, expected: dict) -> float:
    """
    Measures how accurately the agent predicted supplier lead time.
    Score 1.0 = perfect prediction. Score 0.0 = error >= predicted days.
    """
    predicted = output.get("predicted_lead_days", 1)
    error = abs(output.get("prediction_error", 0))
    if predicted == 0:
        return 1.0
    score = 1.0 - (error / predicted)
    return round(max(0.0, min(1.0, score)), 4)


def stockout_score(output: dict, expected: dict) -> float:
    """
    Penalises any days the shelf was empty.
    0 days = perfect. 1 day = partial credit. 2+ days = fail.
    """
    days = output.get("stockout_days", 0)
    if days == 0:
        return 1.0
    elif days == 1:
        return 0.5
    else:
        return 0.0


def waste_score(output: dict, expected: dict) -> float:
    """
    Penalises over-ordering (unsold/expired units).
    Waste < 5% of order = perfect. > 20% = near-fail.
    """
    waste = output.get("waste_units", 0)
    qty = output.get("quantity_ordered", 1)
    if qty == 0:
        return 1.0
    pct = waste / qty
    if pct < 0.05:
        return 1.0
    elif pct < 0.10:
        return 0.7
    elif pct < 0.20:
        return 0.4
    else:
        return 0.1


# ─────────────────────────────────────────────
# BUILD EVAL DATASET
# ─────────────────────────────────────────────

def build_eval_case(order: dict, cycle: int) -> dict:
    """
    Convert a raw purchase_order row into a structured eval case.

    Returns a dict with:
      input    — what the agent knew at decision time
      expected — ideal outcome (zero stockouts, zero waste, zero error)
      actual   — what actually happened (from the database)
    """
    velocity = get_velocity_at_time(order["sku"], order["ordered_at"])
    seasonal = is_seasonal(order["sku"], order["ordered_at"])

    input_data = {
        "sku": order["sku"],
        "cycle": cycle,
        "predicted_lead_days": order.get("predicted_arrival") and _lead_days_from_order(order),
        "predicted_quantity": order["quantity_ordered"],
        "velocity_at_time": velocity,
        "seasonal_flag": seasonal,
        "agent_reasoning": order.get("agent_reasoning", ""),
    }

    expected = {
        "stockout_days": 0,
        "waste_units": 0,
        "prediction_error": 0,
    }

    actual = {
        "sku": order["sku"],
        "cycle": cycle,
        "stockout_days": order.get("stockout_days", 0),
        "waste_units": order.get("waste_units", 0),
        "prediction_error": order.get("prediction_error", 0),
        "predicted_lead_days": input_data["predicted_lead_days"] or 10,
        "quantity_ordered": order["quantity_ordered"],
    }

    return {"input": input_data, "expected": expected, "actual": actual}


def _lead_days_from_order(order: dict) -> int:
    """Compute predicted lead days from ordered_at → predicted_arrival."""
    try:
        ordered = datetime.fromisoformat(order["ordered_at"].replace("Z", "+00:00"))
        if ordered.tzinfo is None:
            ordered = ordered.replace(tzinfo=timezone.utc)
        from datetime import date
        predicted_str = order.get("predicted_arrival")
        if not predicted_str:
            return 10
        predicted = datetime.fromisoformat(predicted_str)
        if predicted.tzinfo is None:
            predicted = predicted.replace(tzinfo=timezone.utc)
        return max(1, (predicted - ordered).days)
    except Exception:
        return 10


# ─────────────────────────────────────────────
# RUN EXPERIMENTS
# ─────────────────────────────────────────────

def run_experiment(name: str, cases: list[dict]):
    """
    Run a single Braintrust experiment for a group of order cycles.
    Each case is scored on lead time accuracy, stockout avoidance, and waste.
    """
    print(f"\nRunning experiment: {name} ({len(cases)} orders)")

    dataset = []
    for case in cases:
        dataset.append(
            {
                "input": case["input"],
                "expected": case["expected"],
                "metadata": {"cycle": case["actual"]["cycle"], "sku": case["actual"]["sku"]},
                # We store actual in input so scorers can access it
                # (Braintrust passes output=task(input), so we use a passthrough task)
                "tags": [f"cycle-{case['actual']['cycle']}", case["actual"]["sku"]],
            }
        )

    # Passthrough task: returns the actual outcomes stored in the database
    # In a real system this would call the live agent; here we replay history.
    actual_map = {
        f"{c['actual']['sku']}-{c['actual']['cycle']}": c["actual"] for c in cases
    }

    def task(input_data: dict) -> dict:
        key = f"{input_data['sku']}-{input_data['cycle']}"
        return actual_map.get(key, {"stockout_days": 0, "waste_units": 0, "prediction_error": 0, "predicted_lead_days": 10, "quantity_ordered": 100})

    scores_collector = []

    async def run():
        results = await Eval(
            name,
            data=dataset,
            task=task,
            scores=[lead_time_accuracy, stockout_score, waste_score],
        )
        return results

    import asyncio
    result = asyncio.run(run())

    # Compute aggregate for console output
    all_scores = []
    for case in cases:
        actual = case["actual"]
        expected = case["expected"]
        s1 = lead_time_accuracy(actual, expected)
        s2 = stockout_score(actual, expected)
        s3 = waste_score(actual, expected)
        overall = round((s1 + s2 + s3) / 3, 4)
        all_scores.append(overall)
        scores_collector.append({
            "sku": actual["sku"],
            "cycle": actual["cycle"],
            "lead_time_accuracy": s1,
            "stockout_score": s2,
            "waste_score": s3,
            "overall": overall,
        })

    avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
    print(f"{name} overall score: {avg}")
    return avg


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    # Initialise Braintrust with API key
    braintrust.init_logger(api_key=BRAINTRUST_API_KEY, project=PROJECT_NAME)

    # Load and enrich all delivered orders
    raw_orders = load_orders()

    # Build eval cases with cycle numbers
    all_cases: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for order in raw_orders:
        cycle = assign_cycle(order["ordered_at"])
        case = build_eval_case(order, cycle)
        all_cases[cycle].append(case)

    # ── Three experiments showing improvement arc ──

    exp_1_2 = all_cases[1] + all_cases[2]
    exp_3_4 = all_cases[3] + all_cases[4]
    exp_5_6 = all_cases[5] + all_cases[6]

    score_1_2 = run_experiment("cycle-1-2", exp_1_2)
    score_3_4 = run_experiment("cycle-3-4", exp_3_4)
    score_5_6 = run_experiment("cycle-5-6", exp_5_6)

    print(f"\n{'='*50}")
    print(f"  Improvement Summary")
    print(f"{'='*50}")
    print(f"  cycle-1-2  (early):   {score_1_2:.2f}")
    print(f"  cycle-3-4  (mid):     {score_3_4:.2f}")
    print(f"  cycle-5-6  (mature):  {score_5_6:.2f}")
    print(f"{'='*50}")
    print(f"\nAll experiments pushed to Braintrust. View at https://braintrust.dev")


if __name__ == "__main__":
    main()
