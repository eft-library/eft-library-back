from confluent_kafka import Producer
import os
from dotenv import load_dotenv
import logging

load_dotenv()

BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER")
LOG_TOPIC = os.getenv("LOG_TOPIC")
NOTIFICATION_TOPIC = os.getenv("NOTIFICATION_TOPIC")
WHERE_AM_I_TOPIC = os.getenv("WHERE_AM_I_TOPIC")

producer_conf = {"bootstrap.servers": BOOTSTRAP_SERVER, "client.id": "fastapi-producer"}
producer = Producer(producer_conf)


def delivery_report(err, msg):
    if err:
        logging.error(f"Delivery failed: {err}")


def produce_message(value: str):
    producer.produce(LOG_TOPIC, value=value.encode("utf-8"), callback=delivery_report)
    producer.poll(0)
    producer.flush(0.2)


def produce_notification(value: str):
    producer.produce(
        NOTIFICATION_TOPIC, value=value.encode("utf-8"), callback=delivery_report
    )
    producer.poll(0)
    producer.flush(0.2)


def produce_where_am_i(value: str):
    producer.produce(
        WHERE_AM_I_TOPIC, value=value.encode("utf-8"), callback=delivery_report
    )
    producer.poll(0)
    producer.flush(0.2)
