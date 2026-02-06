from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.health import HealthResponse
from app.services.cache import get_redis

router = APIRouter(tags=["health"])


@router.get(
    "/health/",
    response_model=HealthResponse,
    summary="Health check",
    responses={
        200: {"description": "All services are healthy"},
        503: {"description": "One or more services are unavailable"},
    },
)
async def health(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> HealthResponse:
    checks: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "unavailable"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())
    status_text = "healthy" if all_ok else "degraded"
    
    return HealthResponse(status=status_text, services=checks)
