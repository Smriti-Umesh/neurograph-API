import json
from datetime import datetime, UTC


def publish_event(channel: str, payload: dict) -> None:
    message = {
        "channel": channel,
        "published_at": datetime.now(UTC).isoformat(),
        "payload": payload,
    }

    print("EVENT PUBLISHED")
    print(json.dumps(message, indent=2, default=str))