"""
UrbanPlannerAgent — analyses housing stock, land use, and infrastructure impacts.

Thinks in terms of neighbourhood change over time, zoning interactions,
transit access, and the physical evolution of cities.
"""
import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

SYSTEM_PROMPT = """You are a senior urban planner who has worked with city governments across the US and Europe.
You think in terms of land use, housing stock, neighbourhood change over time, infrastructure
capacity, zoning interactions, and the physical evolution of cities. You understand how policies
ripple through the built environment over decades. You base your analysis on the demographic
and geographic data provided.

Your focus areas: housing stock turnover, neighbourhood gentrification patterns, infrastructure
strain, transit access for affected populations, long-term land use change, geographic impact
distribution across neighbourhoods.

You will be given:
- A policy description
- Real census data about the affected city
- Real economic indicators
- Recent research and news about similar policies

You must respond with ONLY a valid JSON object — no markdown, no explanation outside the JSON.
The JSON must match this exact schema:
{
  "agent_name": "Urban Planner",
  "verdict": "<one of: HIGH RISK | MODERATE RISK | LOW RISK | BENEFICIAL>",
  "confidence": <float 0.0-1.0>,
  "key_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "key_benefits": ["<benefit 1>", "<benefit 2>", "<benefit 3>"],
  "projection_1yr": "<plain English prediction for year 1>",
  "projection_5yr": "<plain English prediction for year 5>",
  "projection_10yr": "<plain English prediction for year 10>",
  "impact_score": <float 0-100, how severely this policy impacts the city's built environment>,
  "affected_population_pct": <float 0-100, estimated % of city population materially affected>
}"""


def _build_prompt(policy_text: str, city: str, rag_context: list[dict],
                  census_summary: str, economic_summary: str) -> str:
    context_text = "\n\n".join([
        f"[{r['type'].upper()} — {r['source']}]\n{r['text']}"
        for r in rag_context
    ])
    return f"""POLICY TO ANALYSE:
{policy_text}

CITY: {city}

CENSUS DATA:
{census_summary}

ECONOMIC INDICATORS:
{economic_summary}

RELEVANT RESEARCH AND DATA:
{context_text}

Analyse this policy from an urban planning perspective. Consider housing stock effects,
neighbourhood change, gentrification patterns, infrastructure, and geographic distribution
of impacts across different neighbourhoods.
Respond with ONLY the JSON object."""


async def run_urban_planner_agent(
    policy_text: str,
    city: str,
    rag_context: list[dict],
    census_summary: str,
    economic_summary: str,
) -> dict:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=1500,
    )

    prompt = _build_prompt(policy_text, city, rag_context, census_summary, economic_summary)
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]

    for attempt in range(2):
        try:
            response = await llm.ainvoke(messages)
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except (json.JSONDecodeError, Exception) as e:
            if attempt == 1:
                raise RuntimeError(f"Urban Planner agent failed after 2 attempts: {e}")
            print(f"  Urban Planner agent retry (attempt {attempt + 1}): {e}")

    return {}
