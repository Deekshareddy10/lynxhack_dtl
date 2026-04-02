"""
Demo data pre-cache builder.

Fetches all data sources and ingests them into ChromaDB.
Run this once before starting the server to pre-populate the vector store.
"""
import sys
from pathlib import Path

# Allow running this file directly from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
from data.census import get_nyc_census_data
from data.fred import get_economic_context
from data.search import search_policy_context
from rag.pipeline import ingest_policy_data, get_collection_count

DEMO_RESULT_PATH = Path(__file__).parent.parent.parent / "data" / "demo_result.json"


def build_demo_cache() -> int:
    """
    Fetches all three data sources and ingests them into ChromaDB.
    Returns total number of chunks stored.
    Safe to run multiple times — upsert means no duplicates.
    """
    print("=" * 50)
    print("Building URBAN demo cache...")
    print("=" * 50)

    print("\n[1/3] Census data")
    census_df = get_nyc_census_data()

    print("\n[2/3] FRED economic data")
    fred_data = get_economic_context()

    print("\n[3/3] Tavily policy research")
    tavily_results = search_policy_context("rent control cap", "New York City")

    print("\n[4/4] Ingesting into ChromaDB vector store...")
    total_chunks = ingest_policy_data(census_df, fred_data, tavily_results)

    print(f"\n{'=' * 50}")
    print(f"Demo cache built successfully!")
    print(f"  Census tracts ingested: {len(census_df)}")
    print(f"  FRED series ingested:   {len(fred_data)}")
    print(f"  Tavily articles:        {len(tavily_results)}")
    print(f"  Total chunks in store:  {get_collection_count()}")
    print(f"{'=' * 50}")

    return total_chunks


async def generate_demo_result():
    """Run the full NYC rent control simulation and save result to disk."""
    from agents.simulation import run_simulation

    print("\nRunning NYC rent control demo simulation...")
    result = await run_simulation(
        "Cap annual rent increases at 3% per year for all residential properties. "
        "Exemptions for new construction under 10 years old.",
        "New York City"
    )

    DEMO_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEMO_RESULT_PATH, "w") as f:
        json.dump(result.model_dump(), f)

    print(f"\nDemo result saved to {DEMO_RESULT_PATH}")
    print(f"  Overall risk score: {result.overall_risk_score}")
    print(f"  Verdict: {result.overall_verdict}")
    print(f"  Census tracts in map: {len(result.map_data)}")
    return result


if __name__ == "__main__":
    build_demo_cache()
    asyncio.run(generate_demo_result())
