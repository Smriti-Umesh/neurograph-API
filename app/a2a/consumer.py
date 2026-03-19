# app/a2a/consumer.py

import json

from fastapi import HTTPException
from pydantic import ValidationError

from app.a2a.handlers import dispatch_a2a_message
from app.a2a.publisher import publish_a2a_message
from app.a2a.schemas import A2AMessage
from app.core.db import SessionLocal
from app.events.rabbitmq import EXCHANGE_NAME, get_rabbitmq_connection, declare_graph_exchange

A2A_REQUEST_QUEUE = "graph.a2a.requests"
A2A_RESPONSE_ROUTING_KEY = "graph.a2a.responses"


def declare_a2a_queue(channel):
    channel.queue_declare(queue=A2A_REQUEST_QUEUE, durable=True)

    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=A2A_REQUEST_QUEUE,
        routing_key="learn.request",
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=A2A_REQUEST_QUEUE,
        routing_key="query.request",
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=A2A_REQUEST_QUEUE,
        routing_key="decay.request",
    )


def build_success_response(message: A2AMessage, result: dict) -> dict:
    return {
        "message_id": message.message_id,
        "message_type": message.message_type.replace(".request", ".response"),
        "correlation_id": message.correlation_id or message.message_id,
        "sender": "brainnet.a2a.consumer",
        "payload": result,
    }


def build_error_response(raw_message: dict, error_type: str, detail: str) -> dict:
    return {
        "message_id": raw_message.get("message_id", "unknown"),
        "message_type": "error.response",
        "correlation_id": raw_message.get("correlation_id") or raw_message.get("message_id"),
        "sender": "brainnet.a2a.consumer",
        "payload": {
            "error": error_type,
            "detail": detail,
        },
    }


def main():
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    declare_graph_exchange(channel)
    declare_a2a_queue(channel)

    def callback(ch, method, properties, body):
        raw_message = {}

        try:
            raw_message = json.loads(body)
            message = A2AMessage(**raw_message)

            print("A2A REQUEST RECEIVED")
            print(f"routing_key={method.routing_key}")
            print(raw_message)

            db = SessionLocal()
            try:
                result = dispatch_a2a_message(
                    db=db,
                    message_type=message.message_type,
                    payload=message.payload,
                )
            finally:
                db.close()

            response = build_success_response(message, result)

            response_routing_key = message.reply_to or A2A_RESPONSE_ROUTING_KEY
            publish_a2a_message(response_routing_key, response)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except ValidationError as e:
            response = build_error_response(raw_message, "validation_error", str(e))
            publish_a2a_message(A2A_RESPONSE_ROUTING_KEY, response)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except HTTPException as e:
            response = build_error_response(raw_message, "http_error", str(e.detail))
            publish_a2a_message(A2A_RESPONSE_ROUTING_KEY, response)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            response = build_error_response(raw_message, "internal_error", str(e))
            publish_a2a_message(A2A_RESPONSE_ROUTING_KEY, response)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=A2A_REQUEST_QUEUE,
        on_message_callback=callback,
    )

    print("Waiting for A2A requests. Press CTRL+C to stop.")
    channel.start_consuming()


if __name__ == "__main__":
    main()