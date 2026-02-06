import asyncio
import logging

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

kafka_producer: AIOKafkaProducer | None = None

MAX_RETRIES = 5
RETRY_INTERVAL = 3


async def init_kafka_producer(bootstrap_servers: str) -> None:
    global kafka_producer
    if kafka_producer is not None:
        return
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
            await producer.start()
            kafka_producer = producer
            logger.info("Kafka producer connected (attempt %s)", attempt)
            return
        except Exception:
            logger.warning("Kafka producer connect attempt %s/%s failed", attempt, MAX_RETRIES)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_INTERVAL)
    logger.error("Could not connect Kafka producer after %s attempts", MAX_RETRIES)


async def close_kafka_producer() -> None:
    global kafka_producer
    if kafka_producer is None:
        return
    await kafka_producer.stop()
    kafka_producer = None


def get_kafka_producer() -> AIOKafkaProducer:
    if kafka_producer is None:
        raise RuntimeError("Kafka producer is not initialized")
    return kafka_producer
