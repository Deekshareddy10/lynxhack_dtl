"""
URBAN — FastAPI application entry point.

Start the server with:
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, simulate

app = FastAPI(
    title="URBAN Policy Simulation API",
    description="Stress-test government policy before it hits the real world.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(simulate.router)
