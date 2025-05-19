from confluent_kafka import Producer
import os
from dotenv import load_dotenv
import logging

load_dotenv()

BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER")
TOPIC = os.getenv("TOPIC")

producer_conf = {"bootstrap.servers": BOOTSTRAP_SERVER, "client.id": "fastapi-producer"}
producer = Producer(producer_conf)


def delivery_report(err, msg):
    if err:
        logging.error(f"Delivery failed: {err}")
    else:
        logging.info(f"Delivered message to {msg.topic()} [{msg.partition()}]")


def produce_message(value: str):
    producer.produce(TOPIC, value=value.encode("utf-8"), callback=delivery_report)
    producer.poll(0)
