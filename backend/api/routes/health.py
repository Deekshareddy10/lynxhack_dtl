"""GET /health — liveness probe for the backend."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "project": "URBAN"}
