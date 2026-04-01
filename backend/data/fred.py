"""
FRED (Federal Reserve Economic Data) API client.
Pulls macroeconomic time series relevant to NYC rent control simulation.
"""
import os
import requests
import joblib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "NYBPPRIVSA":   "New York Private Housing Units Started",
    "UNRATE":       "US Unemployment Rate",
    "MORTGAGE30US": "30-Year Fixed Mortgage Rate",
    "CUUR0100SAH1": "NYC Metro Area Housing CPI",
}

CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "fred_data.joblib"


def _fetch_series(series_id: str, limit: int = 20) -> list[dict]:
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
        raise RuntimeError(f"FRED API error for {series_id}: {response.status_code}")
    data = response.json()
    if "observations" not in data:
        raise RuntimeError(f"Unexpected FRED response for {series_id}: {data}")
    return [
        {"date": obs["date"], "value": float(obs["value"])}
        for obs in data["observations"]
        if obs["value"] != "."
    ]


def get_economic_context() -> dict:
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
            print(f"  -> {series_id}: latest {latest.get('date')} = {latest.get('value')}")
        except Exception as e:
            print(f"  Warning: Could not fetch {series_id}: {e}")
            result[series_id] = {"description": description, "observations": []}

    joblib.dump(result, CACHE_PATH)
    print(f"  -> Cached to {CACHE_PATH}")
    return result


def get_economic_summary(data: dict) -> str:
    lines = ["Key Economic Indicators (Federal Reserve Data):"]
    for series_id, series_data in data.items():
        obs = series_data.get("observations", [])
        if not obs:
            continue
        latest = obs[0]
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


def test_fred():
    data = get_economic_context()
    print("\nEconomic Summary:")
    print(get_economic_summary(data))
    return data


if __name__ == "__main__":
    test_fred()
