from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always bearer)")
