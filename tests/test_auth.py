from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.core.security import get_password_hash


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, unauth_client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        async def set_user_attrs(obj):
            obj.id = 1
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh.side_effect = set_user_attrs

        response = await unauth_client.post(
            "/register/",
            json={"email": "new@example.com", "password": "securepassword"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["id"] == 1
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, unauth_client, mock_db):
        existing_user = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        response = await unauth_client.post(
            "/register/",
            json={"email": "taken@example.com", "password": "securepassword"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, unauth_client):
        response = await unauth_client.post(
            "/register/",
            json={"email": "not-an-email", "password": "securepassword"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, unauth_client):
        response = await unauth_client.post(
            "/register/",
            json={"email": "user@example.com", "password": "12345"},
        )
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, unauth_client, mock_db):
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.hashed_password = get_password_hash("testpassword")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        response = await unauth_client.post(
            "/token/",
            data={"username": "test@example.com", "password": "testpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, unauth_client, mock_db):
        user = MagicMock()
        user.hashed_password = get_password_hash("correct")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        response = await unauth_client.post(
            "/token/",
            data={"username": "test@example.com", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, unauth_client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = await unauth_client.post(
            "/token/",
            data={"username": "nobody@example.com", "password": "password"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, unauth_client):
        response = await unauth_client.post("/token/", data={})
        assert response.status_code == 422
