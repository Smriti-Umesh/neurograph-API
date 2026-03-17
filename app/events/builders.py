from datetime import datetime, UTC
from uuid import uuid4


def build_edge_learned_event(
    network_id: int,
    edge,
    old_weight: float,
    was_active: bool,
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "edge.learned",
        "timestamp": datetime.now(UTC).isoformat(),
        "network_id": network_id,
        "edge_id": edge.id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "relationship_type": edge.relationship_type,
        "old_weight": old_weight,
        "new_weight": edge.weight,
        "activation_count": edge.activation_count,
        "was_active": was_active,
        "is_active": edge.is_active,
    }


def build_edge_decayed_event(
    network_id: int,
    edge,
    old_weight: float,
    was_active: bool,
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "edge.decayed",
        "timestamp": datetime.now(UTC).isoformat(),
        "network_id": network_id,
        "edge_id": edge.id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "old_weight": old_weight,
        "new_weight": edge.weight,
        "was_active": was_active,
        "is_active": edge.is_active,
    }


def build_edge_archived_event(
    network_id: int,
    edge,
    archive_threshold: float,
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "edge.archived",
        "timestamp": datetime.now(UTC).isoformat(),
        "network_id": network_id,
        "edge_id": edge.id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "final_weight": edge.weight,
        "archive_threshold": archive_threshold,
        "is_active": edge.is_active,
    }


def build_edge_reactivated_event(
    network_id: int,
    edge,
    old_weight: float,
    restore_threshold: float,
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "edge.reactivated",
        "timestamp": datetime.now(UTC).isoformat(),
        "network_id": network_id,
        "edge_id": edge.id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "old_weight": old_weight,
        "new_weight": edge.weight,
        "restore_threshold": restore_threshold,
        "is_active": edge.is_active,
    }