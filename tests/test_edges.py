import pytest
from tests.utils import create_network, create_node

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

def test_learn_creates_new_edge_when_missing(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Node A")
    target_node_id = create_node(client, network_id, "Node B")

    response = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Learning applied successfully"
    assert data["edge"]["network_id"] == network_id
    assert data["edge"]["source_node_id"] == source_node_id
    assert data["edge"]["target_node_id"] == target_node_id
    assert data["edge"]["relationship_type"] == "related_to"
    assert data["edge"]["weight"] == 1.0
    assert data["edge"]["is_active"] is True
    assert data["edge"]["activation_count"] == 1

def test_learn_strengthens_existing_edge(client):
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
    assert create_response.status_code == 201

    learn_response = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )

    assert learn_response.status_code == 200
    data = learn_response.json()

    assert data["message"] == "Learning applied successfully"
    assert data["edge"]["weight"] == 1.1
    assert data["edge"]["activation_count"] == 1
    assert data["edge"]["is_active"] is True

def test_learn_repeatedly_strengthens_edge(client):
    network_id = create_network(client)
    source_node_id = create_node(client, network_id, "Node A")
    target_node_id = create_node(client, network_id, "Node B")

    first_response = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    assert second_response.status_code == 200

    data = second_response.json()

    assert data["edge"]["weight"] == 1.1
    assert data["edge"]["activation_count"] == 2
    assert data["edge"]["is_active"] is True

def test_learn_with_missing_source_node_returns_404(client):
    network_id = create_network(client)
    target_node_id = create_node(client, network_id, "Target Node")

    response = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": 999,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Source node not found"}

def test_decay_reduces_weight_of_active_edges(client):
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
    assert create_response.status_code == 201

    decay_response = client.post(f"/networks/{network_id}/decay")
    assert decay_response.status_code == 200

    data = decay_response.json()
    assert data["message"] == "Decay applied successfully"
    assert len(data["decayed_edges"]) == 1
    assert data["decayed_edges"][0]["weight"] == pytest.approx(0.8)
    assert data["decayed_edges"][0]["is_active"] is True

def test_decay_archives_edge_below_threshold(client):
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
    assert create_response.status_code == 201

    client.post(f"/networks/{network_id}/decay") 
    client.post(f"/networks/{network_id}/decay")  
    client.post(f"/networks/{network_id}/decay")  
    final_response = client.post(f"/networks/{network_id}/decay")

    assert final_response.status_code == 200
    data = final_response.json()

    assert len(data["decayed_edges"]) == 1
    assert data["decayed_edges"][0]["weight"] == pytest.approx(0.2)
    assert data["decayed_edges"][0]["is_active"] is False

def test_decay_does_not_affect_archived_edges(client):
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

    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")  # archived at 0.2

    decay_again_response = client.post(f"/networks/{network_id}/decay")
    assert decay_again_response.status_code == 200

    get_response = client.get(f"/edges/{edge_id}")
    assert get_response.status_code == 200
    edge_data = get_response.json()

    assert edge_data["weight"] == 0.2
    assert edge_data["is_active"] is False

def test_decay_does_not_affect_archived_edges(client):
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

    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")  # archived at 0.2

    decay_again_response = client.post(f"/networks/{network_id}/decay")
    assert decay_again_response.status_code == 200

    get_response = client.get(f"/edges/{edge_id}")
    assert get_response.status_code == 200
    edge_data = get_response.json()

    assert edge_data["weight"] == pytest.approx(0.2)
    assert edge_data["is_active"] is False

def test_decay_returns_empty_list_when_no_active_edges(client):
    network_id = create_network(client)

    response = client.post(f"/networks/{network_id}/decay")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Decay applied successfully",
        "decayed_edges": [],
    }

def test_archived_edge_stays_inactive_until_restore_threshold(client):
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

    client.post(f"/networks/{network_id}/decay")  # 1.0 -> 0.8
    client.post(f"/networks/{network_id}/decay")  # 0.8 -> 0.6
    client.post(f"/networks/{network_id}/decay")  # 0.6 -> 0.4
    client.post(f"/networks/{network_id}/decay")  # 0.4 -> 0.2 archived

    first_learn = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    assert first_learn.status_code == 200
    first_data = first_learn.json()

    assert first_data["edge"]["weight"] == pytest.approx(0.3)
    assert first_data["edge"]["is_active"] is False

    second_learn = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    assert second_learn.status_code == 200
    second_data = second_learn.json()

    assert second_data["edge"]["weight"] == pytest.approx(0.4)
    assert second_data["edge"]["is_active"] is False

def test_archived_edge_reactivates_when_restore_threshold_reached(client):
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

    client.post(f"/networks/{network_id}/decay")  # 1.0 -> 0.8
    client.post(f"/networks/{network_id}/decay")  # 0.8 -> 0.6
    client.post(f"/networks/{network_id}/decay")  # 0.6 -> 0.4
    client.post(f"/networks/{network_id}/decay")  # 0.4 -> 0.2 archived

    client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )  # 0.2 -> 0.3

    client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )  # 0.3 -> 0.4

    third_learn = client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )  # 0.4 -> 0.5 reactivate

    assert third_learn.status_code == 200
    data = third_learn.json()

    assert data["edge"]["weight"] == pytest.approx(0.5)
    assert data["edge"]["is_active"] is True
    assert data["edge"]["activation_count"] == 3

def test_reactivated_edge_can_decay_again(client):
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

    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")  # archived at 0.2

    client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )
    client.post(
        f"/networks/{network_id}/learn",
        json={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": "related_to",
        },
    )  # reactivated at 0.5

    decay_response = client.post(f"/networks/{network_id}/decay")
    assert decay_response.status_code == 200

    get_response = client.get(f"/edges/{edge_id}")
    assert get_response.status_code == 200
    edge_data = get_response.json()

    assert edge_data["weight"] == pytest.approx(0.3)
    assert edge_data["is_active"] is False

def test_query_returns_directly_connected_active_node(client):
    network_id = create_network(client)
    node_a = create_node(client, network_id, "Node A")
    node_b = create_node(client, network_id, "Node B")

    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": node_a,
            "target_node_id": node_b,
            "relationship_type": "related_to",
        },
    )

    response = client.post(
    f"/networks/{network_id}/query",
    json={
        "seed_node_ids": [node_a],
        "max_hops": 1,
        "min_score": 0.05,
    },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Query completed successfully"
    assert len(data["results"]) == 1
    assert data["results"][0]["node_id"] == node_b
    assert data["results"][0]["score"] == pytest.approx(0.5)
    assert data["results"][0]["path"] == [node_a, node_b]


def test_query_ignores_archived_edges(client):
    network_id = create_network(client)
    node_a = create_node(client, network_id, "Node A")
    node_b = create_node(client, network_id, "Node B")

    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": node_a,
            "target_node_id": node_b,
            "relationship_type": "related_to",
        },
    )

    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")
    client.post(f"/networks/{network_id}/decay")  # archived

    response = client.post(
    f"/networks/{network_id}/query",
    json={
        "seed_node_ids": [node_a],
        "max_hops": 1,
        "min_score": 0.05,
    },
)

    assert response.status_code == 200
    data = response.json()

    assert data["results"] == []

def test_query_missing_seed_node_returns_404(client):
    network_id = create_network(client)

    response = client.post(
    f"/networks/{network_id}/query",
    json={
        "seed_node_ids": [999],
        "max_hops": 2,
        "min_score": 0.05,
    },
)

    assert response.status_code == 404
    assert "Seed node(s) not found" in response.json()["detail"]

def test_query_seed_node_from_different_network_returns_400(client):
    network_a = create_network(client, "Network A")
    network_b = create_network(client, "Network B")

    seed_node_id = create_node(client, network_b, "Foreign Node")

    response = client.post(
    f"/networks/{network_a}/query",
    json={
    "seed_node_ids": [seed_node_id],
    "max_hops": 2,
    "min_score": 0.05,
},
)

    assert response.status_code == 400
    assert response.json() == {
    "detail": "All seed nodes must belong to the specified network"
}
    
def test_query_single_seed_still_works(client):
    network_id = create_network(client)
    node_a = create_node(client, network_id, "Node A")
    node_b = create_node(client, network_id, "Node B")

    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": node_a,
            "target_node_id": node_b,
            "relationship_type": "related_to",
        },
    )

    response = client.post(
        f"/networks/{network_id}/query",
        json={
            "seed_node_ids": [node_a],
            "max_hops": 4,
            "min_score": 0.05,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) == 1
    assert data["results"][0]["node_id"] == node_b
    assert data["results"][0]["score"] == pytest.approx(0.5)
    assert data["results"][0]["path"] == [node_a, node_b]

def test_query_multiple_seeds_returns_results(client):
    network_id = create_network(client)
    node_a = create_node(client, network_id, "Node A")
    node_b = create_node(client, network_id, "Node B")
    node_c = create_node(client, network_id, "Node C")
    node_d = create_node(client, network_id, "Node D")

    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": node_a,
            "target_node_id": node_b,
            "relationship_type": "related_to",
        },
    )
    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": node_c,
            "target_node_id": node_d,
            "relationship_type": "related_to",
        },
    )

    response = client.post(
        f"/networks/{network_id}/query",
        json={
            "seed_node_ids": [node_a, node_c],
            "max_hops": 4,
            "min_score": 0.05,
        },
    )

    assert response.status_code == 200
    data = response.json()

    returned_ids = {result["node_id"] for result in data["results"]}
    assert returned_ids == {node_b, node_d}

def test_query_min_score_prunes_weak_paths(client):
    network_id = create_network(client)
    node_a = create_node(client, network_id, "Node A")
    node_b = create_node(client, network_id, "Node B")
    node_c = create_node(client, network_id, "Node C")

    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": node_a,
            "target_node_id": node_b,
            "relationship_type": "related_to",
        },
    )
    client.post(
        f"/networks/{network_id}/edges",
        json={
            "source_node_id": node_b,
            "target_node_id": node_c,
            "relationship_type": "related_to",
        },
    )

    response = client.post(
        f"/networks/{network_id}/query",
        json={
            "seed_node_ids": [node_a],
            "max_hops": 4,
            "min_score": 0.3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) == 1
    assert data["results"][0]["node_id"] == node_b
    assert data["results"][0]["score"] == pytest.approx(0.5)

def test_query_missing_seed_nodes_return_404(client):
    network_id = create_network(client)

    response = client.post(
        f"/networks/{network_id}/query",
        json={
            "seed_node_ids": [999],
            "max_hops": 4,
            "min_score": 0.05,
        },
    )

    assert response.status_code == 404
    assert "Seed node(s) not found" in response.json()["detail"]


def test_query_missing_seed_nodes_return_404(client):
    network_id = create_network(client)

    response = client.post(
        f"/networks/{network_id}/query",
        json={
            "seed_node_ids": [999],
            "max_hops": 4,
            "min_score": 0.05,
        },
    )

    assert response.status_code == 404
    assert "Seed node(s) not found" in response.json()["detail"]
