"""
Tavily web search client for live policy research.

Runs targeted searches to find real-world evidence about policy outcomes —
what happened when similar policies were tried elsewhere.
Results are cached per (policy, city) pair.
"""
import os
import re
import joblib
from pathlib import Path
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
CACHE_DIR = Path(__file__).parent.parent.parent / "data"


def _sanitise_filename(text: str) -> str:
    """Turn arbitrary text into a safe filename component."""
    return re.sub(r"[^a-z0-9_]", "_", text.lower())[:40]


def search_policy_context(policy_topic: str, city: str) -> list[dict]:
    """
    Runs 3 targeted web searches and returns up to 15 deduplicated results.

    Each result has: title, url, content (truncated to 500 chars), score.
    Results are cached to disk per (policy_topic, city) pair.
    """
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY is not set in your .env file")

    cache_file = CACHE_DIR / f"tavily_{_sanitise_filename(policy_topic)}_{_sanitise_filename(city)}.joblib"

    if cache_file.exists():
        print(f"Loading Tavily results from cache: {cache_file.name}")
        return joblib.load(cache_file)

    client = TavilyClient(api_key=TAVILY_API_KEY)

    queries = [
        f"{policy_topic} {city} outcomes results data",
        f"{policy_topic} economic impact study research",
        f"{city} housing policy effects 2020 2021 2022 2023 2024",
    ]

    seen_urls: set[str] = set()
    all_results: list[dict] = []

    print(f"Searching Tavily for: '{policy_topic}' in {city}...")
    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=7,
                include_answer=False,
            )
            for r in response.get("results", []):
                url = r.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                content = r.get("content", "")
                all_results.append({
                    "title": r.get("title", ""),
                    "url": url,
                    "content": content[:500],
                    "score": r.get("score", 0.0),
                })
        except Exception as e:
            print(f"  Warning: Tavily query failed: '{query}' — {e}")

    # Sort by relevance score descending, keep top 15
    all_results.sort(key=lambda x: x["score"], reverse=True)
    all_results = all_results[:15]

    print(f"  -> Found {len(all_results)} unique results")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(all_results, cache_file)
    print(f"  -> Cached to {cache_file.name}")

    return all_results


# ── Quick test ────────────────────────────────────────────────────────────────
def test_tavily():
    results = search_policy_context("rent control cap", "New York City")
    print("\nTop 3 results:")
    for r in results[:3]:
        print(f"\n  [{r['score']:.2f}] {r['title']}")
        print(f"  {r['url']}")
        print(f"  {r['content'][:200]}...")
    return results


if __name__ == "__main__":
    test_tavily()
