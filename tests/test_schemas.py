import pytest
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderItem, OrderUpdate
from app.schemas.token import Token
from app.schemas.user import UserCreate
from pydantic import ValidationError


class TestOrderItem:
    def test_valid(self):
        item = OrderItem(product_id="PROD-001", quantity=2, price=10.5)
        assert item.product_id == "PROD-001"
        assert item.quantity == 2
        assert item.price == 10.5

    def test_zero_quantity(self):
        with pytest.raises(ValidationError):
            OrderItem(product_id="PROD-001", quantity=0, price=10.0)

    def test_negative_quantity(self):
        with pytest.raises(ValidationError):
            OrderItem(product_id="PROD-001", quantity=-1, price=10.0)

    def test_zero_price(self):
        with pytest.raises(ValidationError):
            OrderItem(product_id="PROD-001", quantity=1, price=0)

    def test_negative_price(self):
        with pytest.raises(ValidationError):
            OrderItem(product_id="PROD-001", quantity=1, price=-5.0)

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            OrderItem()


class TestOrderCreate:
    def test_valid(self):
        order = OrderCreate(
            items=[{"product_id": "P1", "quantity": 1, "price": 10.0}],
            total_price=10.0,
        )
        assert len(order.items) == 1
        assert order.total_price == 10.0

    def test_empty_items(self):
        with pytest.raises(ValidationError):
            OrderCreate(items=[], total_price=10.0)

    def test_zero_total_price(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                items=[{"product_id": "P1", "quantity": 1, "price": 10.0}],
                total_price=0,
            )

    def test_multiple_items(self):
        order = OrderCreate(
            items=[
                {"product_id": "P1", "quantity": 2, "price": 50.0},
                {"product_id": "P2", "quantity": 1, "price": 30.0},
            ],
            total_price=130.0,
        )
        assert len(order.items) == 2

    def test_invalid_item_in_list(self):
        with pytest.raises(ValidationError):
            OrderCreate(
                items=[{"product_id": "P1", "quantity": -1, "price": 10.0}],
                total_price=10.0,
            )


class TestOrderUpdate:
    def test_valid_statuses(self):
        for status in OrderStatus:
            update = OrderUpdate(status=status)
            assert update.status == status

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            OrderUpdate(status="INVALID")


class TestUserCreate:
    def test_valid(self):
        user = UserCreate(email="user@example.com", password="secure123")
        assert user.email == "user@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="secure123")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", password="12345")

    def test_min_password_length(self):
        user = UserCreate(email="user@example.com", password="123456")
        assert len(user.password) == 6


class TestToken:
    def test_defaults(self):
        token = Token(access_token="abc123")
        assert token.access_token == "abc123"
        assert token.token_type == "bearer"

    def test_explicit_type(self):
        token = Token(access_token="abc", token_type="Bearer")
        assert token.token_type == "Bearer"
