import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import from_url
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import auth, health, orders
from app.core.config import get_settings
from app.core.ratelimit import limiter
from app.messaging.producer import close_kafka_producer, init_kafka_producer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    redis = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    application.state.redis = redis
    await init_kafka_producer(settings.kafka_bootstrap_servers)
    logger.info("Application startup complete")
    yield
    await close_kafka_producer()
    await redis.close()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health)
    application.include_router(auth)
    application.include_router(orders)

    return application


app = create_app()
