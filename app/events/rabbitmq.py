import os
import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

EXCHANGE_NAME = "graph.events"
EXCHANGE_TYPE = "direct"


def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(
        username=RABBITMQ_USERNAME,
        password=RABBITMQ_PASSWORD,
    )

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials,
    )

    return pika.BlockingConnection(parameters)


def declare_graph_exchange(channel):
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type=EXCHANGE_TYPE,
        durable=True,
    )
DEBUG_QUEUE_NAME = "graph.events.debug"


def declare_debug_queue(channel):
    channel.queue_declare(queue=DEBUG_QUEUE_NAME, durable=True)
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=DEBUG_QUEUE_NAME,
        routing_key="graph.edge.learned",
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=DEBUG_QUEUE_NAME,
        routing_key="graph.edge.decayed",
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=DEBUG_QUEUE_NAME,
        routing_key="graph.edge.archived",
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=DEBUG_QUEUE_NAME,
        routing_key="graph.edge.reactivated",
    )