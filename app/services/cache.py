import json

from fastapi import Request
from redis.asyncio import Redis

from app.schemas.order import OrderRead


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


async def get_cached_order(redis: Redis, order_id: str) -> OrderRead | None:
    cached = await redis.get(f"order:{order_id}")
    if not cached:
        return None
    data = json.loads(cached)
    return OrderRead.model_validate(data)


async def set_cached_order(redis: Redis, order: OrderRead) -> None:
    await redis.setex(f"order:{order.id}", 300, order.model_dump_json())
