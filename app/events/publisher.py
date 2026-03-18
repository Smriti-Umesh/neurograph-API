import json

import pika

from app.events.rabbitmq import (
    EXCHANGE_NAME,
    declare_debug_queue,
    declare_graph_exchange,
    get_rabbitmq_connection,
)



def publish_event(channel: str, payload: dict) -> None:
    body = json.dumps(payload)

    connection = get_rabbitmq_connection()
    try:
        rabbit_channel = connection.channel()
        declare_graph_exchange(rabbit_channel)
        declare_debug_queue(rabbit_channel)

        rabbit_channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=channel,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistent message
            ),
        )

        print(f"EVENT PUBLISHED TO RABBITMQ: {channel}")
        print(body)
    finally:
        connection.close()
    
