from tests.utils import create_network

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