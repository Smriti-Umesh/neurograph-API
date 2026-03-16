# tests/utils.py
def create_network(client, name="Test Network"):
    response = client.post("/networks/", json={"name": name})
    return response.json()["id"]

def create_node(client, network_id, label, node_type="concept"):
    response = client.post(
        f"/networks/{network_id}/nodes",
        json={"label": label, "node_type": node_type},
    )
    return response.json()["id"]

def create_edge(client, network_id, source_node_id, target_node_id, relationship_type="related_to"):
    response = client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": relationship_type,
        },
    )
    return response