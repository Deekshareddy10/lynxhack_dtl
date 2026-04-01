"""
Pydantic models for URBAN API request/response contracts.

These models are shared across the FastAPI routes and the agent layer —
they define the shape of every object that flows through the system.
"""
from pydantic import BaseModel, Field
from typing import Optional


class PolicyInput(BaseModel):
    """Incoming request to the /simulate endpoint."""
    policy_text: str = Field(..., description="Full text of the policy being simulated")
    city: str = Field(default="New York City", description="City the policy applies to")


class AgentVerdict(BaseModel):
    """
    Output from a single AI agent.
    Each of the three agents (Economist, Urban Planner, Equity Analyst)
    returns one of these.
    """
    agent_name: str
    verdict: str  # "HIGH RISK" | "MODERATE RISK" | "LOW RISK" | "BENEFICIAL"
    confidence: float = Field(..., ge=0.0, le=1.0)
    key_risks: list[str] = Field(..., min_length=3, max_length=3)
    key_benefits: list[str] = Field(..., min_length=3, max_length=3)
    projection_1yr: str
    projection_5yr: str
    projection_10yr: str
    impact_score: float = Field(..., ge=0, le=100)
    affected_population_pct: float = Field(..., ge=0, le=100)


class TractImpact(BaseModel):
    """Per-census-tract impact data used to colour the Mapbox map."""
    tract_id: str
    impact_score: float = Field(..., ge=0, le=100)
    agent_breakdown: dict[str, float]  # {"economist": 72.0, "planner": 68.0, "equity": 81.0}


class SimulationResult(BaseModel):
    """
    Full result returned by the simulation engine.
    Contains all three agent verdicts + map data.
    """
    simulation_id: str
    policy_text: str
    city: str
    agents: list[AgentVerdict]
    overall_risk_score: float = Field(..., ge=0, le=100)
    overall_verdict: str  # aggregate of the three agents
    map_data: list[TractImpact]
    summary: Optional[str] = None  # one-paragraph plain English summary
