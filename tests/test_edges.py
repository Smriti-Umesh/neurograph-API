# tests/test_edges.py
def create_network(client, name="Edge Test Network"):
    response = client.post("/networks/", json={"name": name})
    return response.json()["id"]


def create_node(client, network_id, label, node_type="concept"):
    response = client.post(
        f"/networks/{network_id}/nodes",
        json={"label": label, "node_type": node_type},
    )
    return response.json()["id"]


def test_create_edge_between_valid_nodes(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Node A")
    target_node_id = create_node(client, network_id, "Node B")

    response = client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["network_id"] == network_id
    assert data["source_node_id"] == source_node_id
    assert data["target_node_id"] == target_node_id
    assert data["relationship_type"] == "related_to"
    assert data["weight"] == 1.0
    assert data["is_active"] is True
    assert data["activation_count"] == 0

def test_create_edge_with_missing_source_node_returns_404(client):
    network_id = create_network(client)
    target_node_id = create_node(client, network_id, "Target Node")

    response = client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": 999,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Source node not found"}


def test_create_edge_with_missing_target_node_returns_404(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Source Node")

    response = client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": 999,
            "relationship_type": "related_to",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Target node not found"}


def test_create_edge_with_nodes_from_different_networks_returns_400(client):
    network_a = create_network(client, "Network A")
    network_b = create_network(client, "Network B")

    source_node_id = create_node(client, network_a, "Node A1")
    target_node_id = create_node(client, network_b, "Node B1")

    response = client.post(
        f"/networks/{network_a}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Both nodes must belong to the specified network"
    }


def test_list_edges_for_network(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Node A")
    target_node_id = create_node(client, network_id, "Node B")

    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )

    response = client.get(f"/networks/{network_id}/edges")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["relationship_type"] == "related_to"
    assert data[0]["weight"] == 1.0
    assert data[0]["is_active"] is True
    assert data[0]["activation_count"] == 0


def test_get_edge_by_id(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Node A")
    target_node_id = create_node(client, network_id, "Node B")

    create_response = client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    edge_id = create_response.json()["id"]

    response = client.get(f"/edges/{edge_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == edge_id
    assert data["relationship_type"] == "related_to"
    assert data["weight"] == 1.0
    assert data["is_active"] is True
    assert data["activation_count"] == 0


def test_update_edge(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Node A")
    target_node_id = create_node(client, network_id, "Node B")

    create_response = client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    edge_id = create_response.json()["id"]

    response = client.patch(
        f"/edges/{edge_id}",
        json={"relationship_type": "strongly_related_to"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["relationship_type"] == "strongly_related_to"
    assert data["weight"] == 1.0
    assert data["is_active"] is True
    assert data["activation_count"] == 0


def test_delete_edge(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Node A")
    target_node_id = create_node(client, network_id, "Node B")

    create_response = client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    edge_id = create_response.json()["id"]

    delete_response = client.delete(f"/edges/{edge_id}")
    assert delete_response.status_code == 204
    assert delete_response.text == ""

    get_response = client.get(f"/edges/{edge_id}")
    assert get_response.status_code == 404 