# app/a2a/publisher.py

import json
import pika

from app.events.rabbitmq import (
    EXCHANGE_NAME,
    declare_graph_exchange,
    get_rabbitmq_connection,
)


def publish_a2a_message(routing_key: str, payload: dict) -> None:
    body = json.dumps(payload)

    connection = get_rabbitmq_connection()
    try:
        channel = connection.channel()
        declare_graph_exchange(channel)

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )

        print(f"A2A MESSAGE PUBLISHED: {routing_key}")
        print(body)
    finally:
        connection.close()