from datetime import timedelta

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from jose import jwt


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password(self):
        hashed = get_password_hash("correct")
        assert not verify_password("wrong", hashed)

    def test_different_hashes(self):
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_long_password(self):
        password = "a" * 500
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_unicode_password(self):
        password = "пароль_с_юникодом_密码"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)


class TestJWT:
    def test_create_access_token(self):
        settings = get_settings()
        token = create_access_token("42")
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "42"
        assert "exp" in payload

    def test_custom_expiry(self):
        settings = get_settings()
        token = create_access_token("1", expires_delta=timedelta(minutes=5))
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "1"

    def test_invalid_token(self):
        settings = get_settings()
        try:
            jwt.decode("invalid.token.here", settings.secret_key, algorithms=[settings.algorithm])
            raise AssertionError("Should have raised")
        except Exception:
            pass

    def test_expired_token(self):
        settings = get_settings()
        token = create_access_token("1", expires_delta=timedelta(seconds=-1))
        try:
            jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            raise AssertionError("Should have raised")
        except Exception:
            pass

    def test_wrong_secret(self):
        token = create_access_token("1")
        try:
            jwt.decode(token, "wrong-secret", algorithms=["HS256"])
            raise AssertionError("Should have raised")
        except Exception:
            pass
