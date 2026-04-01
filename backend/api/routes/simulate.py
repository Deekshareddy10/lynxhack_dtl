from fastapi import APIRouter, HTTPException
from api.models import PolicyInput, SimulationResult

router = APIRouter()


@router.post("/simulate", response_model=SimulationResult)
async def simulate(policy: PolicyInput):
    # TODO Day 2 Step 7
    raise HTTPException(status_code=501, detail="Simulation engine not yet implemented")


@router.get("/demo", response_model=SimulationResult)
async def demo():
    # TODO Day 4 Step 11
    raise HTTPException(status_code=501, detail="Demo cache not yet generated")
