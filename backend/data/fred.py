"""
FRED (Federal Reserve Economic Data) API client.

Pulls macroeconomic time series relevant to NYC rent control simulation.
Data is cached to disk so we only hit the API once per series.
"""
import os
import requests
import joblib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Series relevant to our rent control simulation
SERIES = {
    "CUSR0100SEHA": "Rent of Primary Residence CPI (shelter inflation)",
    "NYBPPRIVSA":   "New York Private Housing Units Started",
    "UNRATE":       "US Unemployment Rate",
    "MORTGAGE30US": "30-Year Fixed Mortgage Rate",
    "CUUR0100SAH1": "NYC Metro Area Housing CPI",
}

CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "fred_data.joblib"


def _fetch_series(series_id: str, limit: int = 20) -> list[dict]:
    """Fetch the most recent observations for one FRED series."""
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY is not set in your .env file")

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
        "observation_start": "2014-01-01",
    }

    response = requests.get(FRED_BASE_URL, params=params, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(f"FRED API error for {series_id}: {response.status_code} {response.text[:200]}")

    data = response.json()

    if "observations" not in data:
        raise RuntimeError(f"Unexpected FRED response for {series_id}: {data}")

    # Filter out missing values (FRED uses "." for unavailable data)
    return [
        {"date": obs["date"], "value": float(obs["value"])}
        for obs in data["observations"]
        if obs["value"] != "."
    ]


def get_economic_context() -> dict:
    """
    Returns all FRED series data, checking disk cache first.
    Shape: {series_id: {"description": str, "observations": list[{date, value}]}}
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_PATH.exists():
        print("Loading FRED data from cache...")
        return joblib.load(CACHE_PATH)

    print("Fetching economic data from FRED API...")
    result = {}
    for series_id, description in SERIES.items():
        try:
            obs = _fetch_series(series_id)
            result[series_id] = {"description": description, "observations": obs}
            latest = obs[0] if obs else {}
            print(f"  -> {series_id}: {len(obs)} observations, latest {latest.get('date')} = {latest.get('value')}")
        except Exception as e:
            print(f"  Warning: Could not fetch {series_id}: {e}")
            result[series_id] = {"description": description, "observations": []}

    joblib.dump(result, CACHE_PATH)
    print(f"  -> Cached to {CACHE_PATH}")
    return result


def get_economic_summary(data: dict) -> str:
    """
    Produces a plain-English summary of key economic indicators.
    Injected into each agent's prompt for grounding.
    """
    lines = ["Key Economic Indicators (Federal Reserve Data):"]

    for series_id, series_data in data.items():
        obs = series_data.get("observations", [])
        if not obs:
            continue
        latest = obs[0]
        # obs is sorted descending, so obs[0] is most recent, obs[-1] is oldest
        oldest = obs[-1]
        description = series_data["description"]

        try:
            pct_change = ((latest["value"] - oldest["value"]) / oldest["value"]) * 100
            lines.append(
                f"- {description}: {latest['value']:.1f} (as of {latest['date']}, "
                f"{pct_change:+.1f}% change over {len(obs)} observations)"
            )
        except (TypeError, ZeroDivisionError):
            lines.append(f"- {description}: {latest['value']} (as of {latest['date']})")

    return "\n".join(lines)


# ── Quick test ────────────────────────────────────────────────────────────────
def test_fred():
    data = get_economic_context()
    print("\nEconomic Summary:")
    print(get_economic_summary(data))
    return data


if __name__ == "__main__":
    test_fred()
