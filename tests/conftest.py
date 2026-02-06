from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes import auth, health, orders
from app.core.security import get_current_user, get_password_hash
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.cache import get_redis


def create_test_app() -> FastAPI:
    application = FastAPI()
    application.include_router(health)
    application.include_router(auth)
    application.include_router(orders)
    return application


@pytest.fixture
def test_user() -> User:
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.hashed_password = get_password_hash("testpassword")
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def test_order() -> Order:
    order = MagicMock(spec=Order)
    order.id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    order.user_id = 1
    order.items = [{"product_id": "PROD-001", "quantity": 2, "price": 50.0}]
    order.total_price = 100.0
    order.status = OrderStatus.PENDING
    order.created_at = datetime.now(timezone.utc)
    return order


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.ping = AsyncMock()
    return redis


@pytest.fixture
async def client(mock_db, mock_redis, test_user):
    app = create_test_app()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_current_user] = lambda: test_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def unauth_client(mock_db, mock_redis):
    app = create_test_app()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
