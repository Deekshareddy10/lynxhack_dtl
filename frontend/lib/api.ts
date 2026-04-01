// TypeScript interfaces matching the FastAPI Pydantic models exactly

export interface AgentVerdict {
  agent_name: string;
  verdict: 'HIGH RISK' | 'MODERATE RISK' | 'LOW RISK' | 'BENEFICIAL';
  confidence: number;
  key_risks: string[];
  key_benefits: string[];
  projection_1yr: string;
  projection_5yr: string;
  projection_10yr: string;
  impact_score: number;
  affected_population_pct: number;
}

export interface TractImpact {
  tract_id: string;
  impact_score: number;
  agent_breakdown: Record<string, number>;
}

export interface SimulationResult {
  simulation_id: string;
  policy_text: string;
  city: string;
  agents: AgentVerdict[];
  overall_risk_score: number;
  overall_verdict: string;
  map_data: TractImpact[];
  summary?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function simulatePolicy(
  policyText: string,
  city: string
): Promise<SimulationResult> {
  const res = await fetch(`${API_URL}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ policy_text: policyText, city }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Simulation failed: ${res.status}`);
  }
  return res.json();
}

export async function getDemo(): Promise<SimulationResult> {
  const res = await fetch(`${API_URL}/demo`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Demo failed: ${res.status}`);
  }
  return res.json();
}
