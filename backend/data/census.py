"""
US Census ACS 5-Year API client.

Fetches demographic and housing data for all census tracts in
New York County (Manhattan, FIPS: state=36, county=061).

Data is cached to disk with joblib so we only hit the API once.
"""
import os
import requests
import pandas as pd
import joblib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

# ACS 5-Year 2022 endpoint
ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

# Variables we need — each maps to a human-readable column name
VARIABLES = {
    "B01003_001E": "population",
    "B19013_001E": "median_income",
    "B25064_001E": "median_rent",
    "B25070_010E": "severely_burdened",   # households paying 50%+ income on rent
    "B17001_002E": "poverty_pop",
    "B03002_003E": "white_pop",           # Non-Hispanic White
    "B03002_012E": "hispanic_pop",        # Hispanic/Latino
    "B03002_004E": "black_pop",           # Black/African American
}

# Cache file location (gitignored)
CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "nyc_census.joblib"


def _fetch_from_api() -> pd.DataFrame:
    """Hit the Census API and return a clean DataFrame."""
    variable_list = ",".join(VARIABLES.keys())

    params = {
        "get": f"NAME,{variable_list}",
        "for": "tract:*",
        "in": "state:36 county:061",   # New York state, New York County (Manhattan)
    }
    # Key is optional — Census API works without it at lower rate limits.
    # Add it when the key activates (can take up to 24hrs after signup).
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    print("Fetching NYC census data from Census ACS API...")
    response = requests.get(ACS_URL, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"Census API returned {response.status_code}: {response.text[:500]}"
        )

    # Census returns HTML when the key is invalid instead of an error status code.
    # Detect this and retry without the key (API works without key at lower rate limits).
    if response.text.strip().startswith("<"):
        print("  Warning: Census API key is not yet active — retrying without key...")
        params.pop("key", None)
        response = requests.get(ACS_URL, params=params, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Census API returned {response.status_code}: {response.text[:500]}")

    data = response.json()

    # First row is the header
    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    # Build a clean tract_id from state + county + tract FIPS codes
    df["tract_id"] = df["state"] + df["county"] + df["tract"]

    # Rename Census variable codes to readable names
    df = df.rename(columns=VARIABLES)

    # Keep only the columns we care about
    keep_cols = ["tract_id"] + list(VARIABLES.values())
    df = df[keep_cols]

    # Convert numeric columns from strings (Census API returns everything as strings)
    numeric_cols = list(VARIABLES.values())
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop tracts with no population data (suppressed cells)
    df = df.dropna(subset=["population"])
    df = df[df["population"] > 0]

    # Derived metric: what % of the tract is severely rent-burdened
    df["rent_burden_pct"] = (df["severely_burdened"] / df["population"] * 100).round(2)

    # Derived metric: minority population percentage (for equity analysis)
    df["minority_pct"] = (
        (df["hispanic_pop"] + df["black_pop"]) / df["population"] * 100
    ).round(2)

    df = df.reset_index(drop=True)
    print(f"  -> Fetched {len(df)} census tracts in New York County")
    return df


def get_nyc_census_data() -> pd.DataFrame:
    """
    Returns a DataFrame of NYC census tract demographics.
    Checks the disk cache first — only hits the API if cache is missing.
    """
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_PATH.exists():
        print("Loading NYC census data from cache...")
        return joblib.load(CACHE_PATH)

    df = _fetch_from_api()
    joblib.dump(df, CACHE_PATH)
    print(f"  -> Cached to {CACHE_PATH}")
    return df


def get_census_summary(df: pd.DataFrame) -> str:
    """
    Produces a plain-English summary of key NYC housing stats.
    This is injected into each agent's prompt as economic context.
    """
    total_pop = int(df["population"].sum())
    median_rent = int(df["median_rent"].median())
    median_income = int(df["median_income"].median())
    avg_burden_pct = df["rent_burden_pct"].mean()
    severely_burdened_tracts = int((df["rent_burden_pct"] > 30).sum())
    total_tracts = len(df)

    return (
        f"New York County (Manhattan) Census Summary:\n"
        f"- Total population across {total_tracts} census tracts: {total_pop:,}\n"
        f"- Median gross rent: ${median_rent:,}/month\n"
        f"- Median household income: ${median_income:,}/year\n"
        f"- Average share of residents severely rent-burdened (50%+ income on rent): {avg_burden_pct:.1f}%\n"
        f"- Census tracts where >30% of residents are severely rent-burdened: {severely_burdened_tracts}/{total_tracts}\n"
        f"- Rent-to-income ratio (annualised): {(median_rent * 12 / median_income * 100):.0f}%"
    )


# ── Quick test ────────────────────────────────────────────────────────────────
def test_census():
    df = get_nyc_census_data()
    print("\nFirst 5 tracts:")
    print(df[["tract_id", "population", "median_income", "median_rent", "rent_burden_pct"]].head())
    print("\nCensus Summary:")
    print(get_census_summary(df))
    return df


if __name__ == "__main__":
    test_census()
