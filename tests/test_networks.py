# tests/test_networks.py
def test_create_network(client):
    response = client.post("/networks/", json={"name": "Test Network"})

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Network"


def test_list_networks(client):
    client.post("/networks/", json={"name": "Network A"})
    client.post("/networks/", json={"name": "Network B"})

    response = client.get("/networks/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Network A"
    assert data[1]["name"] == "Network B"


def test_get_network_by_id(client):
    create_response = client.post("/networks/", json={"name": "My Network"})
    network_id = create_response.json()["id"]

    response = client.get(f"/networks/{network_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == network_id
    assert data["name"] == "My Network"


def test_get_missing_network_returns_404(client):
    response = client.get("/networks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Error: Network not found"}


def test_update_network(client):
    create_response = client.post("/networks/", json={"name": "Old Name"})
    network_id = create_response.json()["id"]

    response = client.patch(
        f"/networks/{network_id}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == network_id
    assert data["name"] == "Updated Name"


def test_delete_network(client):
    create_response = client.post("/networks/", json={"name": "Delete Me"})
    network_id = create_response.json()["id"]

    delete_response = client.delete(f"/networks/{network_id}")
    assert delete_response.status_code == 204
    assert delete_response.text == ""

    get_response = client.get(f"/networks/{network_id}")
    assert get_response.status_code == 404