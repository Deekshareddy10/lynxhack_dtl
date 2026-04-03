#  Government Policy Simulation Platform

> Stress-test policy before it hits the real world.

CivicLens lets policymakers upload any policy, pulls live economic and demographic data, runs three specialised AI agents (Economist, Urban Planner, Equity Analyst), and renders the projected impact on an interactive 3D Mapbox map.

---

## Required Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Powers all AI agents (console.anthropic.com) |
| `MAPBOX_TOKEN` | 3D map rendering (account.mapbox.com) |
| `CENSUS_API_KEY` | US Census ACS data (api.data.gov/signup) |
| `FRED_API_KEY` | Federal Reserve economic time series (fred.stlouisfed.org) |
| `TAVILY_API_KEY` | Live web search for policy context (tavily.com) |
| `NEWS_API_KEY` | Recent news about policy outcomes (newsapi.org) |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox GL JS token |
| `NEXT_PUBLIC_API_URL` | Backend API URL (e.g. http://localhost:8000) |

---

## Quick Start

```bash
# Backend
cd backend
poetry install
cp .env.example .env   # fill in your keys
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local   # fill in your keys
npm run dev
```

Open http://localhost:3000
