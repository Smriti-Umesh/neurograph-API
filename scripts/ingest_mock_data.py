import json
import requests

BASE_URL = "http://127.0.0.1:8000"


DATA_PATH = "data/mock_relationships.json"


def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_existing_nodes():
    response = requests.get(f"{BASE_URL}/networks/{NETWORK_ID}/nodes")
    response.raise_for_status()
    nodes = response.json()

    # map label -> node_id
    return {node["label"]: node["id"] for node in nodes}


def create_node(label):
    payload = {
        "label": label,
        "node_type": "concept",
    }

    response = requests.post(
        f"{BASE_URL}/networks/{NETWORK_ID}/nodes",
        json=payload,
    )
    response.raise_for_status()
    node = response.json()

    print(f"Created node: {label} (id={node['id']})")

    return node["id"]


def learn_edge(source_id, target_id, relationship_type):
    payload = {
        "source_node_id": source_id,
        "target_node_id": target_id,
        "relationship_type": relationship_type,
    }

    response = requests.post(
        f"{BASE_URL}/networks/{NETWORK_ID}/learn",
        json=payload,
    )
    response.raise_for_status()

    print(f"Learned: {source_id} -> {target_id} ({relationship_type})")


def main():
    data = load_data()
    node_map = get_existing_nodes()

    for item in data:
        source_label = item["source_label"]
        target_label = item["target_label"]
        relationship_type = item["relationship_type"]

        # ensure source node exists
        if source_label not in node_map:
            node_map[source_label] = create_node(source_label)

        # ensure target node exists
        if target_label not in node_map:
            node_map[target_label] = create_node(target_label)

        source_id = node_map[source_label]
        target_id = node_map[target_label]

        learn_edge(source_id, target_id, relationship_type)


if __name__ == "__main__":
    main()