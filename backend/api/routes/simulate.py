"""
POST /simulate — triggers the full 3-agent simulation pipeline
GET  /demo     — returns pre-cached NYC rent control result instantly
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from api.models import PolicyInput, SimulationResult
from agents.simulation import run_simulation

router = APIRouter()

DEMO_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "demo_result.json"


@router.post("/simulate", response_model=SimulationResult)
async def simulate(policy: PolicyInput):
    try:
        result = await run_simulation(policy.policy_text, policy.city)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/demo", response_model=SimulationResult)
async def demo():
    if not DEMO_CACHE_PATH.exists():
        # No cache yet — run the simulation live
        result = await run_simulation(
            "Cap annual rent increases at 3% per year for all residential properties. "
            "Exemptions for new construction under 10 years old.",
            "New York City"
        )
        return result

    with open(DEMO_CACHE_PATH) as f:
        data = json.load(f)
    return SimulationResult(**data)
