import os
import sys
from pathlib import Path
from uuid import uuid4

import requests
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.a2a.publisher import publish_a2a_message

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


# -------------------------
# API lookup helpers
# -------------------------

def list_networks():
    response = requests.get(f"{BASE_URL}/networks/", timeout=30)
    response.raise_for_status()
    return response.json()


def get_network_id_by_name(network_name: str) -> int:
    networks = list_networks()

    for network in networks:
        if network["name"] == network_name:
            return network["id"]

    raise ValueError(f"Network not found with name: {network_name}")


def list_nodes(network_id: int):
    response = requests.get(f"{BASE_URL}/networks/{network_id}/nodes", timeout=30)
    response.raise_for_status()
    return response.json()


def list_edges(network_id: int):
    response = requests.get(f"{BASE_URL}/networks/{network_id}/edges", timeout=30)
    response.raise_for_status()
    return response.json()


def get_node_id_by_label(network_id: int, label: str) -> int:
    nodes = list_nodes(network_id)

    for node in nodes:
        if node["label"] == label:
            return node["id"]

    raise ValueError(f"Node not found in network {network_id} with label: {label}")


def find_first_node_by_type(network_id: int, node_type: str) -> dict:
    nodes = list_nodes(network_id)

    for node in nodes:
        if node["node_type"] == node_type:
            return node

    raise ValueError(f"No node found in network {network_id} with node_type: {node_type}")


def find_first_paper_with_active_outgoing_edge(network_id: int) -> dict:
    nodes = list_nodes(network_id)
    edges = list_edges(network_id)

    node_by_id = {node["id"]: node for node in nodes}

    active_source_ids = {
        edge["source_node_id"]
        for edge in edges
        if edge["is_active"] is True
    }

    for node in nodes:
        if node["node_type"] == "paper" and node["id"] in active_source_ids:
            return node

    raise ValueError(
        f"No paper node with at least one active outgoing edge found in network {network_id}"
    )


# -------------------------
# A2A send helpers
# -------------------------

def send_learn_request(network_name: str, source_label: str, target_label: str, relationship_type: str):
    network_id = get_network_id_by_name(network_name)
    source_node_id = get_node_id_by_label(network_id, source_label)
    target_node_id = get_node_id_by_label(network_id, target_label)

    payload = {
        "message_id": str(uuid4()),
        "message_type": "learn.request",
        "correlation_id": str(uuid4()),
        "reply_to": "graph.a2a.responses",
        "sender": "dynamic.test.client",
        "payload": {
            "network_id": network_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": relationship_type,
        },
    }

    print("Sending learn request:")
    print(payload)

    publish_a2a_message("learn.request", payload)


def send_query_request(network_name: str, seed_label: str, max_hops: int = 4, min_score: float = 0.05):
    network_id = get_network_id_by_name(network_name)
    seed_node_id = get_node_id_by_label(network_id, seed_label)

    payload = {
        "message_id": str(uuid4()),
        "message_type": "query.request",
        "correlation_id": str(uuid4()),
        "reply_to": "graph.a2a.responses",
        "sender": "dynamic.test.client",
        "payload": {
            "network_id": network_id,
            "seed_node_ids": [seed_node_id],
            "max_hops": max_hops,
            "min_score": min_score,
        },
    }

    print("Sending query request:")
    print(payload)

    publish_a2a_message("query.request", payload)


def send_decay_request(network_name: str):
    network_id = get_network_id_by_name(network_name)

    payload = {
        "message_id": str(uuid4()),
        "message_type": "decay.request",
        "correlation_id": str(uuid4()),
        "reply_to": "graph.a2a.responses",
        "sender": "dynamic.test.client",
        "payload": {
            "network_id": network_id,
        },
    }

    print("Sending decay request:")
    print(payload)

    publish_a2a_message("decay.request", payload)


def send_query_for_first_paper_with_active_edge(network_name: str):
    network_id = get_network_id_by_name(network_name)
    paper_node = find_first_paper_with_active_outgoing_edge(network_id)

    print(
        f"Using paper with active outgoing edge as seed: "
        f"{paper_node['label']} (id={paper_node['id']})"
    )

    payload = {
        "message_id": str(uuid4()),
        "message_type": "query.request",
        "correlation_id": str(uuid4()),
        "reply_to": "graph.a2a.responses",
        "sender": "dynamic.test.client",
        "payload": {
            "network_id": network_id,
            "seed_node_ids": [paper_node["id"]],
            "max_hops": 4,
            "min_score": 0.05,
        },
    }

    print("Sending query request:")
    print(payload)

    publish_a2a_message("query.request", payload)


# -------------------------
# CLI
# -------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/send_a2a_message.py learn <network_name> <source_label> <target_label> [relationship_type]")
        print("  python scripts/send_a2a_message.py query <network_name> <seed_label>")
        print("  python scripts/send_a2a_message.py decay <network_name>")
        print("  python scripts/send_a2a_message.py query-active-paper <network_name>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "learn":
        if len(sys.argv) < 5:
            print("Usage: python scripts/send_a2a_message.py learn <network_name> <source_label> <target_label> [relationship_type]")
            sys.exit(1)

        network_name = sys.argv[2]
        source_label = sys.argv[3]
        target_label = sys.argv[4]
        relationship_type = sys.argv[5] if len(sys.argv) > 5 else "related_to"

        send_learn_request(network_name, source_label, target_label, relationship_type)

    elif command == "query":
        if len(sys.argv) < 4:
            print("Usage: python scripts/send_a2a_message.py query <network_name> <seed_label>")
            sys.exit(1)

        network_name = sys.argv[2]
        seed_label = sys.argv[3]

        send_query_request(network_name, seed_label)

    elif command == "decay":
        if len(sys.argv) < 3:
            print("Usage: python scripts/send_a2a_message.py decay <network_name>")
            sys.exit(1)

        network_name = sys.argv[2]
        send_decay_request(network_name)

    elif command == "query-active-paper":
        if len(sys.argv) < 3:
            print("Usage: python scripts/send_a2a_message.py query-active-paper <network_name>")
            sys.exit(1)

        network_name = sys.argv[2]
        send_query_for_first_paper_with_active_edge(network_name)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()