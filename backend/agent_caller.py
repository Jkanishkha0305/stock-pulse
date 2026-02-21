"""
Call Airia pipeline (webhook) with context. Used at the start of run_cycle to inform the agent.
"""
import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv
load_dotenv()


def build_agent_context(
    prioritized_skus: list[dict[str, Any]],
    signals: dict[str, Any],
) -> str:
    """Build a string context for the Airia agent (user_input)."""
    summary = {
        "prioritized_products": [
            {
                "sku": p.get("sku"),
                "name": p.get("name"),
                "current_stock": p.get("current_stock"),
                "reorder_point": p.get("reorder_point"),
                "days_remaining": p.get("days_remaining"),
                "velocity_7day_avg": p.get("velocity_7day_avg"),
            }
            for p in prioritized_skus
        ],
        "signals": signals,
    }
    return json.dumps(summary, indent=2)


def call_airia(user_input: str) -> dict[str, Any]:
    """
    POST to Airia webhook (PipelineExecution) with user_input.
    Returns the API response (result, report, etc.) or error dict.
    """
    url = os.getenv("AIRIA_WEBHOOK_URL")
    api_key = os.getenv("AIRIA_API_KEY")
    if not url or not api_key:
        return {"error": "AIRIA_WEBHOOK_URL or AIRIA_API_KEY not set", "result": None}
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key.strip(),
                },
                json={"user_input": user_input},
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        return {"error": str(e), "status_code": e.response.status_code, "result": None}
    except Exception as e:
        return {"error": str(e), "result": None}
