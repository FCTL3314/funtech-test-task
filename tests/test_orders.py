from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.order import OrderStatus


class TestCreateOrder:
    @pytest.mark.asyncio
    @patch("app.api.routes.orders.get_kafka_producer")
    async def test_create_order_success(self, mock_get_producer, client, mock_db, mock_redis):
        mock_producer = AsyncMock()
        mock_get_producer.return_value = mock_producer

        async def set_order_attrs(obj):
            obj.id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            obj.user_id = 1
            obj.items = [{"product_id": "PROD-001", "quantity": 2, "price": 50.0}]
            obj.total_price = 100.0
            obj.status = OrderStatus.PENDING
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh.side_effect = set_order_attrs

        response = await client.post(
            "/orders/",
            json={
                "items": [{"product_id": "PROD-001", "quantity": 2, "price": 50.0}],
                "total_price": 100.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert data["user_id"] == 1
        assert data["total_price"] == 100.0
        assert data["status"] == "PENDING"
        mock_producer.send_and_wait.assert_awaited_once()
        mock_redis.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_order_invalid_items(self, client):
        response = await client.post(
            "/orders/",
            json={"items": [], "total_price": 100.0},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_order_zero_price(self, client):
        response = await client.post(
            "/orders/",
            json={
                "items": [{"product_id": "P1", "quantity": 1, "price": 10.0}],
                "total_price": 0,
            },
        )
        assert response.status_code == 422


class TestGetOrder:
    @pytest.mark.asyncio
    async def test_get_order_success(self, client, mock_db, test_order):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_result

        response = await client.get(f"/orders/{test_order.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_order.id
        assert data["user_id"] == 1

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = await client.get("/orders/a1b2c3d4-e5f6-7890-abcd-ef1234567890/")
        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"

    @pytest.mark.asyncio
    async def test_get_order_forbidden(self, client, mock_db, test_order):
        test_order.user_id = 999
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_result

        response = await client.get(f"/orders/{test_order.id}/")
        assert response.status_code == 403
        assert response.json()["detail"] == "Not allowed"

    @pytest.mark.asyncio
    async def test_get_order_invalid_uuid(self, client):
        response = await client.get("/orders/not-a-uuid/")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_order_from_cache(self, client, mock_redis, test_order):
        import json

        cached_data = {
            "id": test_order.id,
            "user_id": 1,
            "items": [{"product_id": "PROD-001", "quantity": 2, "price": 50.0}],
            "total_price": 100.0,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        response = await client.get(f"/orders/{test_order.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_order.id


class TestUpdateOrder:
    @pytest.mark.asyncio
    async def test_update_order_status(self, client, mock_db, test_order, mock_redis):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_result

        async def apply_status_change(obj):
            obj.status = OrderStatus.PAID

        mock_db.refresh.side_effect = apply_status_change

        response = await client.patch(
            f"/orders/{test_order.id}/",
            json={"status": "PAID"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_order_not_found(self, client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = await client.patch(
            "/orders/a1b2c3d4-e5f6-7890-abcd-ef1234567890/",
            json={"status": "PAID"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_order_forbidden(self, client, mock_db, test_order):
        test_order.user_id = 999
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_result

        response = await client.patch(
            f"/orders/{test_order.id}/",
            json={"status": "PAID"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_order_invalid_status(self, client):
        response = await client.patch(
            "/orders/a1b2c3d4-e5f6-7890-abcd-ef1234567890/",
            json={"status": "UNKNOWN"},
        )
        assert response.status_code == 422


class TestGetUserOrders:
    @pytest.mark.asyncio
    async def test_get_user_orders_success(self, client, mock_db, test_order):
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [test_order]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = await client.get("/orders/user/1/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_order.id

    @pytest.mark.asyncio
    async def test_get_user_orders_empty(self, client, mock_db):
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = await client.get("/orders/user/1/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_user_orders_forbidden(self, client):
        response = await client.get("/orders/user/999/")
        assert response.status_code == 403
        assert response.json()["detail"] == "Not allowed"
