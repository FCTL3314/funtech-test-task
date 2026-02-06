from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class OrderItem(BaseModel):
    product_id: str = Field(description="Product identifier", examples=["PROD-12345"])
    quantity: int = Field(gt=0, description="Quantity of the product", examples=[2])
    price: float = Field(gt=0, description="Price per unit", examples=[99.99])


class OrderCreate(BaseModel):
    items: list[OrderItem] = Field(
        min_length=1,
        description="List of order items",
        examples=[
            [
                {"product_id": "PROD-12345", "quantity": 2, "price": 99.99},
                {"product_id": "PROD-67890", "quantity": 1, "price": 149.99},
            ]
        ],
    )
    total_price: float = Field(gt=0, description="Total price of the order", examples=[349.97])


class OrderUpdate(BaseModel):
    status: OrderStatus = Field(description="New order status")


class OrderRead(BaseModel):
    id: str = Field(description="Order unique identifier")
    user_id: int = Field(description="User ID who created the order")
    items: list[OrderItem | dict[str, Any]] = Field(description="List of order items")
    total_price: float = Field(description="Total price of the order")
    status: OrderStatus = Field(description="Current order status")
    created_at: datetime = Field(description="Order creation timestamp")

    model_config = {"from_attributes": True}
