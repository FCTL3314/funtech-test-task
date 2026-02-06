import asyncio
import json

from aiokafka import AIOKafkaConsumer

from app.core.config import get_settings
from app.tasks.worker import process_order


async def consume() -> None:
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        settings.kafka_topic_new_order,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=True,
        group_id="order-service-consumer",
    )
    await consumer.start()
    try:
        async for message in consumer:
            order_id = message.value.get("order_id")
            if order_id:
                process_order.delay(order_id)
    finally:
        await consumer.stop()


def main() -> None:
    asyncio.run(consume())


if __name__ == "__main__":
    main()
