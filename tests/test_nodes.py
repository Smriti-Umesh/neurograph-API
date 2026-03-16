from tests.utils import create_network, create_node, create_edge

# tests/test_nodes.py
def create_network(client, name="Node Test Network"):
    response = client.post("/networks/", json={"name": name})
    return response.json()["id"]


def test_create_node_in_network(client):
    network_id = create_network(client)

    response = client.post(
        f"/networks/{network_id}/nodes",
        json={
            "label": "Hebbian Learning",
            "node_type": "concept",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["network_id"] == network_id
    assert data["label"] == "Hebbian Learning"
    assert data["node_type"] == "concept"


def test_create_node_in_missing_network_returns_404(client):
    response = client.post(
        "/networks/999/nodes",
        json={
            "label": "Ghost Node",
            "node_type": "concept",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Network not found"}


def test_list_nodes_for_network(client):
    network_id = create_network(client)

    client.post(
        f"/networks/{network_id}/nodes",
        json={"label": "Node A", "node_type": "concept"},
    )
    client.post(
        f"/networks/{network_id}/nodes",
        json={"label": "Node B", "node_type": "author"},
    )

    response = client.get(f"/networks/{network_id}/nodes")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["label"] == "Node A"
    assert data[1]["label"] == "Node B"


def test_get_node_by_id(client):
    network_id = create_network(client)

    create_response = client.post(
        f"/networks/{network_id}/nodes",
        json={"label": "Spreading Activation", "node_type": "concept"},
    )
    node_id = create_response.json()["id"]

    response = client.get(f"/nodes/{node_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == node_id
    assert data["label"] == "Spreading Activation"


def test_get_missing_node_returns_404(client):
    response = client.get("/nodes/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Node not found"}


def test_update_node(client):
    network_id = create_network(client)

    create_response = client.post(
        f"/networks/{network_id}/nodes",
        json={"label": "Old Label", "node_type": "concept"},
    )
    node_id = create_response.json()["id"]

    response = client.patch(
        f"/nodes/{node_id}",
        json={"label": "New Label", "node_type": "concept"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == node_id
    assert data["label"] == "New Label"


def test_delete_node(client):
    network_id = create_network(client)

    create_response = client.post(
        f"/networks/{network_id}/nodes",
        json={"label": "Delete Node", "node_type": "concept"},
    )
    node_id = create_response.json()["id"]

    delete_response = client.delete(f"/nodes/{node_id}")
    assert delete_response.status_code == 204
    assert delete_response.text == ""

    get_response = client.get(f"/nodes/{node_id}")
    assert get_response.status_code == 404
    
