import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.messaging.producer import get_kafka_producer
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate
from app.services.cache import get_cached_order, get_redis, set_cached_order
from app.services.orders import create_order, get_order, get_user_orders, update_order_status

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    responses={
        201: {"description": "Order successfully created"},
        401: {"description": "Not authenticated"},
    },
)
async def create_order_endpoint(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> OrderRead:
    order = await create_order(db, current_user.id, order_in.items, order_in.total_price)
    order_read = OrderRead.model_validate(order)
    await set_cached_order(redis, order_read)

    settings = get_settings()
    producer = get_kafka_producer()
    payload = json.dumps({"order_id": order.id}).encode("utf-8")
    await producer.send_and_wait(settings.kafka_topic_new_order, payload)

    return order_read


@router.get(
    "/{order_id}/",
    response_model=OrderRead,
    summary="Get order by ID",
    responses={
        200: {"description": "Order found"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access to this order is forbidden"},
        404: {"description": "Order not found"},
    },
)
async def get_order_endpoint(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> OrderRead:
    cached = await get_cached_order(redis, str(order_id))
    if cached is not None:
        if cached.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
        return cached

    order = await get_order(db, str(order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    order_read = OrderRead.model_validate(order)
    await set_cached_order(redis, order_read)
    return order_read


@router.patch(
    "/{order_id}/",
    response_model=OrderRead,
    summary="Update order status",
    responses={
        200: {"description": "Order status updated"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access to this order is forbidden"},
        404: {"description": "Order not found"},
    },
)
async def update_order_endpoint(
    order_id: UUID,
    order_in: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> OrderRead:
    order = await get_order(db, str(order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    order = await update_order_status(db, order, order_in.status)
    order_read = OrderRead.model_validate(order)
    await set_cached_order(redis, order_read)
    return order_read


@router.get(
    "/user/{user_id}/",
    response_model=list[OrderRead],
    summary="Get all orders for a user",
    responses={
        200: {"description": "List of user orders"},
        401: {"description": "Not authenticated"},
        403: {"description": "Access to this user's orders is forbidden"},
    },
)
async def get_user_orders_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrderRead]:
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    orders = await get_user_orders(db, user_id)
    return [OrderRead.model_validate(order) for order in orders]
