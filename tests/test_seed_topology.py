import os
import sys

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    class _PytestMock:
        @staticmethod
        def approx(expected, rel=None, abs=None, nan_ok=False):
            class ApproxValue:
                def __init__(self, val, tol):
                    self.val = val
                    self.tol = tol if tol is not None else 1e-6

                def __eq__(self, actual):
                    if isinstance(actual, (int, float)):
                        import builtins
                        return builtins.abs(float(actual) - float(self.val)) <= self.tol
                    return False

                def __repr__(self):
                    return f"approx({self.val} ± {self.tol})"

            tol = abs if abs is not None else rel
            return ApproxValue(expected, tol)

    pytest = _PytestMock()

from unittest.mock import MagicMock, patch
from scripts.seed_mock_topology import (
    generate_normalized_embedding,
    get_seed_cypher,
    get_past_incident_cypher,
    seed_database,
)


def test_generate_normalized_embedding_length_and_unit_norm():
    """Verify that generated 384-dimensional vector embeddings are L2-normalized unit vectors."""
    vec = generate_normalized_embedding(384)
    assert len(vec) == 384, "Vector must have 384 dimensions"
    norm = sum(x * x for x in vec) ** 0.5
    assert pytest.approx(norm, 0.001) == 1.0, f"Expected unit norm 1.0, got {norm}"


def test_seed_cypher_microservices_and_topology():
    """Verify seed Cypher defines all 6 polyglot microservices and cross-service dependencies."""
    cypher = get_seed_cypher()
    expected_services = [
        "FrontendAPI",
        "CheckoutService",
        "PaymentService",
        "InventoryService",
        "NotificationService",
        "AuthService",
    ]
    for svc in expected_services:
        assert svc in cypher, f"Missing microservice: {svc}"

    assert "[:DEPENDS_ON" in cypher, "Must create DEPENDS_ON service edges"


def test_seed_cypher_ast_call_hierarchy_and_commits():
    """Verify seed Cypher defines Endpoints, AST Functions, CALLS edges, and offending Commit."""
    cypher = get_seed_cypher()
    # Endpoints
    assert "/api/v1/charge" in cypher
    assert "/api/v1/checkout" in cypher

    # AST Functions
    assert "process_charge" in cypher
    assert "verify_token" in cypher
    assert "call_webhook" in cypher
    assert "acquire_db_lock" in cypher

    # Git Commit
    assert "c3d9a107" in cypher, "Must include offending commit sha c3d9a107"
    assert "timeout=None" in cypher, "Must include timeout diff snippet in commit"
    assert "MODIFIED_BY" in cypher, "Must link AST Function to Commit via MODIFIED_BY"


def test_seed_cypher_teams_engineers_runbooks():
    """Verify seed Cypher defines Team, Engineer, and procedural Runbook nodes."""
    cypher = get_seed_cypher()
    assert "team_payments" in cypher
    assert "team_sre" in cypher
    assert "eng_alice" in cypher
    assert "eng_bob" in cypher
    assert "rb_net_042" in cypher


def test_get_past_incident_cypher():
    """Verify get_past_incident_cypher creates PastIncident, vector embedding, and relationships."""
    cypher = get_past_incident_cypher()
    assert "PastIncident" in cypher
    assert "postmortem_inc_historical_01" in cypher
    assert "vecf32($vec)" in cypher
    assert "AFFECTED_SERVICE" in cypher
    assert "RESOLVED_BY_PLAYBOOK" in cypher
    assert "svc_payment" in cypher
    assert "rb_net_042" in cypher


def test_seed_database_execution_flow_with_mock():
    """Verify seed_database performs expected initialization, indexing, and query calls."""
    mock_redis_client = MagicMock()
    mock_redis_client.ping.return_value = True

    with patch("scripts.seed_mock_topology.redis") as mock_redis_mod:
        mock_redis_mod.Redis.return_value = mock_redis_client
        success = seed_database(host="mockhost", port=6379, graph="test_graph")
        assert success is True
        mock_redis_client.ping.assert_called_once()
        # Verify commands were executed on the graph
        assert mock_redis_client.execute_command.call_count >= 3


def test_seed_database_handles_offline_falkordb():
    """Verify seed_database returns False gracefully when FalkorDB is unreachable."""
    mock_redis_client = MagicMock()
    mock_redis_client.ping.side_effect = ConnectionError("Could not connect")

    with patch("scripts.seed_mock_topology.redis") as mock_redis_mod:
        mock_redis_mod.Redis.return_value = mock_redis_client
        success = seed_database(host="offlinehost", port=6379, graph="test_graph")
        assert success is False


if __name__ == "__main__":
    print("Running test_generate_normalized_embedding_length_and_unit_norm...")
    test_generate_normalized_embedding_length_and_unit_norm()
    print("PASS: test_generate_normalized_embedding_length_and_unit_norm")

    print("Running test_seed_cypher_microservices_and_topology...")
    test_seed_cypher_microservices_and_topology()
    print("PASS: test_seed_cypher_microservices_and_topology")

    print("Running test_seed_cypher_ast_call_hierarchy_and_commits...")
    test_seed_cypher_ast_call_hierarchy_and_commits()
    print("PASS: test_seed_cypher_ast_call_hierarchy_and_commits")

    print("Running test_seed_cypher_teams_engineers_runbooks...")
    test_seed_cypher_teams_engineers_runbooks()
    print("PASS: test_seed_cypher_teams_engineers_runbooks")

    print("Running test_get_past_incident_cypher...")
    test_get_past_incident_cypher()
    print("PASS: test_get_past_incident_cypher")

    print("Running test_seed_database_execution_flow_with_mock...")
    test_seed_database_execution_flow_with_mock()
    print("PASS: test_seed_database_execution_flow_with_mock")

    print("Running test_seed_database_handles_offline_falkordb...")
    test_seed_database_handles_offline_falkordb()
    print("PASS: test_seed_database_handles_offline_falkordb")

    print("\nAll 7 topology seed tests passed successfully!")
