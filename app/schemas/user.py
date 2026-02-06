from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=6, description="User password (min 6 characters)")


class UserRead(BaseModel):
    id: int = Field(description="User unique identifier")
    email: EmailStr = Field(description="User email address")
    created_at: datetime = Field(description="User registration timestamp")

    model_config = {"from_attributes": True}
