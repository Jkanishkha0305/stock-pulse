"""
External signals for demand: weather, festivals, seasons.
Fetches or computes and returns structured context for the agent.
"""
import os
from datetime import datetime
from typing import Any

import httpx

# Open-Meteo: free, no API key. London as default.
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LAT, DEFAULT_LON = 51.5074, -0.1278  # London

# Static festivals / key dates (UK-oriented; extend as needed)
FESTIVALS = [
    {"name": "Christmas", "month": 12, "day_start": 20, "day_end": 26, "demand_boost_skus": ["SKU-001", "SKU-002"]},
    {"name": "New Year", "month": 1, "day_start": 1, "day_end": 2, "demand_boost_skus": ["SKU-001", "SKU-005"]},
    {"name": "Easter", "month": 4, "day_start": 1, "day_end": 10, "demand_boost_skus": ["SKU-002", "SKU-001"]},
    {"name": "Halloween", "month": 10, "day_start": 28, "day_end": 31, "demand_boost_skus": ["SKU-004"]},
    {"name": "Bonfire Night", "month": 11, "day_start": 5, "day_end": 5, "demand_boost_skus": ["SKU-002", "SKU-005"]},
    {"name": "Black Friday", "month": 11, "day_start": 24, "day_end": 29, "demand_boost_skus": ["SKU-001", "SKU-002", "SKU-005"]},
]


def get_season(now: datetime | None = None) -> dict[str, Any]:
    """Derive season from date. Used for Pumpkin Soup (autumn), Paracetamol (flu season)."""
    now = now or datetime.utcnow()
    month = now.month
    if month in (12, 1, 2):
        season = "winter"
        flu_season = True
        pumpkin_high = False
    elif month in (3, 4, 5):
        season = "spring"
        flu_season = False
        pumpkin_high = False
    elif month in (6, 7, 8):
        season = "summer"
        flu_season = False
        pumpkin_high = False
    else:
        season = "autumn"
        flu_season = True  # Oct-Nov flu
        pumpkin_high = True
    return {
        "season": season,
        "month": month,
        "flu_season": flu_season,
        "pumpkin_soup_high_demand": pumpkin_high,
    }


def get_festivals_today(now: datetime | None = None) -> list[dict[str, Any]]:
    """Return festivals overlapping today (or static list for demo)."""
    now = now or datetime.utcnow()
    m, d = now.month, now.day
    active = []
    for f in FESTIVALS:
        start, end = f["day_start"], f["day_end"]
        if f["month"] == m and start <= d <= end:
            active.append({"name": f["name"], "demand_boost_skus": f.get("demand_boost_skus", [])})
    return active


def fetch_weather(lat: float | None = None, lon: float | None = None) -> dict[str, Any]:
    """Fetch current weather from Open-Meteo (free, no key). Returns temp and conditions."""
    lat = lat or float(os.getenv("WEATHER_LAT", DEFAULT_LAT))
    lon = lon or float(os.getenv("WEATHER_LON", DEFAULT_LON))
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weather_code",
                    "timezone": "Europe/London",
                },
            )
            r.raise_for_status()
            data = r.json()
            current = data.get("current", {})
            return {
                "temperature_c": current.get("temperature_2m"),
                "weather_code": current.get("weather_code"),
                "lat": lat,
                "lon": lon,
            }
    except Exception:
        return {
            "temperature_c": None,
            "weather_code": None,
            "lat": lat,
            "lon": lon,
            "error": "Weather API unavailable",
        }


def get_all_signals(now: datetime | None = None) -> dict[str, Any]:
    """Aggregate weather, festivals, and season for agent context."""
    now = now or datetime.utcnow()
    weather = fetch_weather()
    season = get_season(now)
    festivals = get_festivals_today(now)
    return {
        "weather": weather,
        "season": season,
        "festivals": festivals,
        "date": now.strftime("%Y-%m-%d"),
    }
