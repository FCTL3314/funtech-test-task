import time

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "order_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@celery_app.task(name="process_order")
def process_order(order_id: str) -> None:
    time.sleep(2)
    print(f"Order {order_id} processed")
