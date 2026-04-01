"""
EconomistAgent — analyses fiscal and market impacts of a policy.

Thinks in terms of supply/demand, landlord incentives, market distortions,
city tax revenue, and long-term investment dynamics.
"""
import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

SYSTEM_PROMPT = """You are a senior urban economist with 20 years of experience analysing housing markets.
You think in terms of supply and demand curves, market incentives, fiscal impacts on city budgets,
landlord behaviour, and long-term investment dynamics. You are evidence-based and cite real economic
research where relevant. You are not politically biased — you report what the data and economic
theory predict, even if the findings are uncomfortable.

Your focus areas: rental supply effects, landlord exit rates, black market rents, city tax revenue,
construction investment, economic displacement, market distortions.

You will be given:
- A policy description
- Real census data about the affected city
- Real economic indicators
- Recent research and news about similar policies

You must respond with ONLY a valid JSON object — no markdown, no explanation outside the JSON.
The JSON must match this exact schema:
{
  "agent_name": "Economist",
  "verdict": "<one of: HIGH RISK | MODERATE RISK | LOW RISK | BENEFICIAL>",
  "confidence": <float 0.0-1.0>,
  "key_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "key_benefits": ["<benefit 1>", "<benefit 2>", "<benefit 3>"],
  "projection_1yr": "<plain English prediction for year 1>",
  "projection_5yr": "<plain English prediction for year 5>",
  "projection_10yr": "<plain English prediction for year 10>",
  "impact_score": <float 0-100, how severely this policy impacts the city economically>,
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

Analyse this policy from an economic perspective. Consider supply/demand effects,
landlord incentives, market distortions, fiscal impacts, and long-term investment dynamics.
Respond with ONLY the JSON object."""


async def run_economist_agent(
    policy_text: str,
    city: str,
    rag_context: list[dict],
    census_summary: str,
    economic_summary: str,
) -> dict:
    """
    Runs the Economist agent and returns an AgentVerdict dict.
    Retries once if JSON parsing fails.
    """
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
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except (json.JSONDecodeError, Exception) as e:
            if attempt == 1:
                raise RuntimeError(f"Economist agent failed after 2 attempts: {e}")
            print(f"  Economist agent retry (attempt {attempt + 1}): {e}")

    return {}
