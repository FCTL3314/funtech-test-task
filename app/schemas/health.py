from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Overall health status (healthy/degraded)")
    services: dict[str, str] = Field(description="Status of individual services")
