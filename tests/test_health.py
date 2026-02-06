import pytest


class TestHealth:
    @pytest.mark.asyncio
    async def test_healthy(self, client, mock_db, mock_redis):
        response = await client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["postgres"] == "ok"
        assert data["services"]["redis"] == "ok"

    @pytest.mark.asyncio
    async def test_postgres_down(self, client, mock_db, mock_redis):
        mock_db.execute.side_effect = ConnectionError("pg down")

        response = await client.get("/health/")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["postgres"] == "unavailable"
        assert data["services"]["redis"] == "ok"

    @pytest.mark.asyncio
    async def test_redis_down(self, client, mock_db, mock_redis):
        mock_redis.ping.side_effect = ConnectionError("redis down")

        response = await client.get("/health/")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["postgres"] == "ok"
        assert data["services"]["redis"] == "unavailable"

    @pytest.mark.asyncio
    async def test_all_down(self, client, mock_db, mock_redis):
        mock_db.execute.side_effect = ConnectionError("pg down")
        mock_redis.ping.side_effect = ConnectionError("redis down")

        response = await client.get("/health/")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["postgres"] == "unavailable"
        assert data["services"]["redis"] == "unavailable"
