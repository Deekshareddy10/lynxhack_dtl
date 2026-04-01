"""
POST /simulate  — triggers the full simulation pipeline
GET  /demo      — returns pre-cached NYC rent control result instantly

Both routes are stubs until Day 2 Step 7 wires in the simulation engine.
"""
from fastapi import APIRouter, HTTPException
from api.models import PolicyInput, SimulationResult

router = APIRouter()


@router.post("/simulate", response_model=SimulationResult)
async def simulate(policy: PolicyInput):
    # TODO Day 2 Step 7: call run_simulation() from agents/simulation.py
    raise HTTPException(status_code=501, detail="Simulation engine not yet implemented — come back on Day 2")


@router.get("/demo", response_model=SimulationResult)
async def demo():
    # TODO Day 4 Step 11: load data/demo_result.json and return it
    raise HTTPException(status_code=501, detail="Demo cache not yet generated — come back on Day 4")
