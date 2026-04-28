"""Health check router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "healthy", "service": "lotomind-intelligence"}
