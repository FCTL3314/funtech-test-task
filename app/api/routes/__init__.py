from app.api.routes.auth import router as auth
from app.api.routes.health import router as health
from app.api.routes.orders import router as orders

__all__ = ["auth", "health", "orders"]
