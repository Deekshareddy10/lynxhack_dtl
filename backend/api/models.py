"""Pydantic models for URBAN API request/response contracts."""
from pydantic import BaseModel, Field
from typing import Optional


class PolicyInput(BaseModel):
    policy_text: str = Field(..., description="Full text of the policy being simulated")
    city: str = Field(default="New York City", description="City the policy applies to")


class AgentVerdict(BaseModel):
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
    tract_id: str
    impact_score: float = Field(..., ge=0, le=100)
    agent_breakdown: dict[str, float]


class SimulationResult(BaseModel):
    simulation_id: str
    policy_text: str
    city: str
    agents: list[AgentVerdict]
    overall_risk_score: float = Field(..., ge=0, le=100)
    overall_verdict: str
    map_data: list[TractImpact]
    summary: Optional[str] = None
