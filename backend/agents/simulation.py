"""
LangGraph simulation orchestrator.

Runs all three agents in parallel using asyncio.gather(), then combines
their verdicts into a SimulationResult with per-tract map data.

Flow: fetch_context → run_agents (parallel) → combine_results
"""
import asyncio
import uuid
from typing import TypedDict

from langgraph.graph import StateGraph, END

from agents.economist import run_economist_agent
from agents.urban_planner import run_urban_planner_agent
from agents.equity_analyst import run_equity_analyst_agent
from data.census import get_nyc_census_data, get_census_summary
from data.fred import get_economic_context, get_economic_summary
from data.search import search_policy_context
from rag.pipeline import retrieve
from api.models import AgentVerdict, SimulationResult, TractImpact


class SimulationState(TypedDict):
    policy_text: str
    city: str
    rag_context: list[dict]
    census_summary: str
    economic_summary: str
    economist_verdict: dict
    planner_verdict: dict
    equity_verdict: dict
    combined_result: dict


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def fetch_context(state: SimulationState) -> SimulationState:
    """Load cached data and retrieve relevant RAG chunks for this policy."""
    print(f"  [1/3] Fetching context for: {state['policy_text'][:60]}...")

    census_df = get_nyc_census_data()
    fred_data = get_economic_context()

    census_sum = get_census_summary(census_df)
    econ_sum = get_economic_summary(fred_data)

    # Retrieve semantically relevant chunks for this specific policy
    rag_chunks = retrieve(
        query=f"{state['policy_text']} {state['city']} housing rent economic impact",
        k=8,
    )

    return {
        **state,
        "rag_context": rag_chunks,
        "census_summary": census_sum,
        "economic_summary": econ_sum,
    }


async def run_agents(state: SimulationState) -> SimulationState:
    """Run all three agents IN PARALLEL — cuts total time from ~45s to ~20s."""
    print("  [2/3] Running agents in parallel...")

    economist_task = run_economist_agent(
        state["policy_text"], state["city"],
        state["rag_context"], state["census_summary"], state["economic_summary"]
    )
    planner_task = run_urban_planner_agent(
        state["policy_text"], state["city"],
        state["rag_context"], state["census_summary"], state["economic_summary"]
    )
    equity_task = run_equity_analyst_agent(
        state["policy_text"], state["city"],
        state["rag_context"], state["census_summary"], state["economic_summary"]
    )

    economist, planner, equity = await asyncio.gather(
        economist_task, planner_task, equity_task
    )

    return {
        **state,
        "economist_verdict": economist,
        "planner_verdict": planner,
        "equity_verdict": equity,
    }


async def combine_results(state: SimulationState) -> SimulationState:
    """
    Merge the three agent verdicts into a SimulationResult.
    Generates per-census-tract impact scores for the Mapbox map.
    """
    print("  [3/3] Combining results and generating map data...")

    verdicts_raw = [
        state["economist_verdict"],
        state["planner_verdict"],
        state["equity_verdict"],
    ]

    # Parse each agent verdict (fill defaults if a field is missing)
    agents = []
    for v in verdicts_raw:
        agents.append(AgentVerdict(
            agent_name=v.get("agent_name", "Unknown"),
            verdict=v.get("verdict", "MODERATE RISK"),
            confidence=float(v.get("confidence", 0.5)),
            key_risks=v.get("key_risks", ["Unknown", "Unknown", "Unknown"])[:3],
            key_benefits=v.get("key_benefits", ["Unknown", "Unknown", "Unknown"])[:3],
            projection_1yr=v.get("projection_1yr", ""),
            projection_5yr=v.get("projection_5yr", ""),
            projection_10yr=v.get("projection_10yr", ""),
            impact_score=float(v.get("impact_score", 50.0)),
            affected_population_pct=float(v.get("affected_population_pct", 50.0)),
        ))

    # Weighted average: equity weighted higher for rent control (most direct human impact)
    weights = {"Economist": 0.35, "Urban Planner": 0.30, "Equity Analyst": 0.35}
    overall_risk = sum(
        a.impact_score * weights.get(a.agent_name, 0.33)
        for a in agents
    )

    # Determine overall verdict from average
    if overall_risk >= 70:
        overall_verdict = "HIGH RISK"
    elif overall_risk >= 45:
        overall_verdict = "MODERATE RISK"
    elif overall_risk >= 25:
        overall_verdict = "LOW RISK"
    else:
        overall_verdict = "BENEFICIAL"

    # Generate per-tract impact scores for the map
    # Each tract's score is driven by rent burden (how exposed to rent control)
    # and poverty rate (vulnerability) — normalised 0-100
    census_df = get_nyc_census_data()
    equity_score = float(state["equity_verdict"].get("impact_score", 50.0))

    map_data = []
    max_burden = census_df["rent_burden_pct"].max() or 1
    max_minority = census_df["minority_pct"].max() or 1

    for _, row in census_df.iterrows():
        # Tract score: blend of rent burden, minority pct (equity proxy), and overall risk
        burden_norm = (row["rent_burden_pct"] / max_burden) * 100
        minority_norm = (row["minority_pct"] / max_minority) * 100
        tract_score = round(
            0.4 * burden_norm +
            0.3 * minority_norm +
            0.3 * overall_risk,
            1
        )
        map_data.append(TractImpact(
            tract_id=str(row["tract_id"]),
            impact_score=min(tract_score, 100.0),
            agent_breakdown={
                "economist": float(state["economist_verdict"].get("impact_score", 50)),
                "planner": float(state["planner_verdict"].get("impact_score", 50)),
                "equity": equity_score,
            }
        ))

    result = SimulationResult(
        simulation_id=str(uuid.uuid4()),
        policy_text=state["policy_text"],
        city=state["city"],
        agents=agents,
        overall_risk_score=round(overall_risk, 1),
        overall_verdict=overall_verdict,
        map_data=map_data,
        summary=(
            f"Analysis of '{state['policy_text'][:80]}...' in {state['city']}. "
            f"Overall risk score: {overall_risk:.0f}/100 ({overall_verdict}). "
            f"{len(map_data)} census tracts analysed."
        ),
    )

    return {**state, "combined_result": result.model_dump()}


# ── Build the LangGraph ───────────────────────────────────────────────────────

def _build_graph():
    graph = StateGraph(SimulationState)
    graph.add_node("fetch_context", fetch_context)
    graph.add_node("run_agents", run_agents)
    graph.add_node("combine_results", combine_results)

    graph.set_entry_point("fetch_context")
    graph.add_edge("fetch_context", "run_agents")
    graph.add_edge("run_agents", "combine_results")
    graph.add_edge("combine_results", END)

    return graph.compile()


_graph = None


async def run_simulation(policy_text: str, city: str) -> SimulationResult:
    """
    Main entry point — runs the full simulation pipeline.
    Called by the /simulate API route.
    """
    global _graph
    if _graph is None:
        _graph = _build_graph()

    print(f"\nRunning URBAN simulation...")
    initial_state: SimulationState = {
        "policy_text": policy_text,
        "city": city,
        "rag_context": [],
        "census_summary": "",
        "economic_summary": "",
        "economist_verdict": {},
        "planner_verdict": {},
        "equity_verdict": {},
        "combined_result": {},
    }

    final_state = await _graph.ainvoke(initial_state)
    return SimulationResult(**final_state["combined_result"])
