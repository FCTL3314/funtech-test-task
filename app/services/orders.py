from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.schemas.order import OrderItem


async def create_order(
    db: AsyncSession,
    user_id: int,
    items: list[OrderItem],
    total_price: float,
) -> Order:
    items_dict = [item.model_dump() for item in items]
    order = Order(user_id=user_id, items=items_dict, total_price=total_price, status=OrderStatus.PENDING)
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def get_order(db: AsyncSession, order_id: str) -> Order | None:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def update_order_status(
    db: AsyncSession,
    order: Order,
    status: OrderStatus,
) -> Order:
    order.status = status
    await db.commit()
    await db.refresh(order)
    return order


async def get_user_orders(db: AsyncSession, user_id: int) -> list[Order]:
    result = await db.execute(select(Order).where(Order.user_id == user_id))
    return list(result.scalars().all())
