import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.events.rabbitmq import DEBUG_QUEUE_NAME, get_rabbitmq_connection

# This is a simple consumer script that can be used to 
#  print messages from the debug queue.
def main():
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    def callback(ch, method, properties, body):
        print("RECEIVED EVENT")
        print(f"routing_key={method.routing_key}")
        print(json.loads(body))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=DEBUG_QUEUE_NAME,
        on_message_callback=callback,
    )

    print("Waiting for events. Press CTRL+C to stop.")
    channel.start_consuming()


if __name__ == "__main__":
    main()