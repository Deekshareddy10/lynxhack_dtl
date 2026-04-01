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
ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

VARIABLES = {
    "B01003_001E": "population",
    "B19013_001E": "median_income",
    "B25064_001E": "median_rent",
    "B25070_010E": "severely_burdened",
    "B17001_002E": "poverty_pop",
    "B03002_003E": "white_pop",
    "B03002_012E": "hispanic_pop",
    "B03002_004E": "black_pop",
}

CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "nyc_census.joblib"


def _fetch_from_api() -> pd.DataFrame:
    variable_list = ",".join(VARIABLES.keys())
    params = {
        "get": f"NAME,{variable_list}",
        "for": "tract:*",
        "in": "state:36 county:061",
    }
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    print("Fetching NYC census data from Census ACS API...")
    response = requests.get(ACS_URL, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Census API returned {response.status_code}: {response.text[:500]}")

    # Census returns HTML when the key is invalid — detect and retry without key
    if response.text.strip().startswith("<"):
        print("  Warning: Census API key not yet active — retrying without key...")
        params.pop("key", None)
        response = requests.get(ACS_URL, params=params, timeout=30)

    data = response.json()
    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)
    df["tract_id"] = df["state"] + df["county"] + df["tract"]
    df = df.rename(columns=VARIABLES)

    keep_cols = ["tract_id"] + list(VARIABLES.values())
    df = df[keep_cols]

    for col in VARIABLES.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["population"])
    df = df[df["population"] > 0]
    df["rent_burden_pct"] = (df["severely_burdened"] / df["population"] * 100).round(2)
    df["minority_pct"] = ((df["hispanic_pop"] + df["black_pop"]) / df["population"] * 100).round(2)
    df = df.reset_index(drop=True)

    print(f"  -> Fetched {len(df)} census tracts in New York County")
    return df


def get_nyc_census_data() -> pd.DataFrame:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        print("Loading NYC census data from cache...")
        return joblib.load(CACHE_PATH)
    df = _fetch_from_api()
    joblib.dump(df, CACHE_PATH)
    print(f"  -> Cached to {CACHE_PATH}")
    return df


def get_census_summary(df: pd.DataFrame) -> str:
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
        f"- Average share of residents severely rent-burdened: {avg_burden_pct:.1f}%\n"
        f"- Tracts where >30% of residents are severely rent-burdened: {severely_burdened_tracts}/{total_tracts}\n"
        f"- Rent-to-income ratio (annualised): {(median_rent * 12 / median_income * 100):.0f}%"
    )


def test_census():
    df = get_nyc_census_data()
    print("\nFirst 5 tracts:")
    print(df[["tract_id", "population", "median_income", "median_rent", "rent_burden_pct"]].head())
    print("\nCensus Summary:")
    print(get_census_summary(df))
    return df


if __name__ == "__main__":
    test_census()
