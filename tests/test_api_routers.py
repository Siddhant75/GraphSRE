import os
import sys
from unittest.mock import patch, AsyncMock

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    class _PytestMock:
        class mark:
            @staticmethod
            def asyncio(fn):
                return fn
    pytest = _PytestMock()

from backend.main import app

try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
except (ImportError, Exception):
    class FallbackTestResponse:
        def __init__(self, status_code: int, json_data: dict):
            self.status_code = status_code
            self._json = json_data

        def json(self):
            return self._json

    class FallbackTestClient:
        def __init__(self, target_app):
            self.app = target_app

        def get(self, url: str, **kwargs):
            res = self.app.test_request("GET", url, **kwargs)
            return FallbackTestResponse(res.get("status_code", 200), res.get("data", {}))

        def post(self, url: str, json: dict = None, **kwargs):
            res = self.app.test_request("POST", url, json_payload=json, **kwargs)
            return FallbackTestResponse(res.get("status_code", 200), res.get("data", {}))

    client = FallbackTestClient(app)


def test_health_check_endpoint():
    """Verify backend health check returns status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "graphsre-backend"


@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_triage_incident_endpoint(mock_query):
    """Verify POST /api/incidents/triage triggers triage and returns severity and blast radius."""
    mock_query.return_value = [
        ["incident_id", "severity", "blast_radius", "impacted_services", "sev_score"],
        [["inc_triage_99", "SEV_1", 3, ["CheckoutService", "FrontendAPI"], 91.2]]
    ]
    payload = {
        "alert_id": "alt_socket_01",
        "fingerprint": "fp_sha256_stripe_read_timeout",
        "alert_name": "PaymentService_SocketReadTimeout",
        "source": "Prometheus",
        "target_service": "PaymentService",
        "metric_value": 4850.0,
        "threshold": 500.0,
        "timestamp": 1718900000000
    }
    response = client.post("/api/incidents/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    assert data["severity"] == "SEV_1"
    assert data["blast_radius"] == 3
    assert "CheckoutService" in data["impacted_services"]


@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_get_blackboard_snapshot_endpoint(mock_query):
    """Verify GET /api/incidents/{incident_id}/blackboard returns incident graph snapshot."""
    mock_query.return_value = [
        ["incident_id", "lifecycle_state", "severity", "blast_radius", "started_at", "alerts", "hypotheses"],
        [
            [
                "inc_triage_99",
                "HYPOTHESIS_FORMED",
                "SEV_1",
                3,
                1718900000000,
                [{"name": "PaymentService_SocketReadTimeout", "metric_value": 4850.0}],
                [{"hypothesis_id": "hyp_01", "statement": "Socket timeout missing", "confidence": 0.915}]
            ]
        ]
    ]
    response = client.get("/api/incidents/inc_triage_99/blackboard")
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == "inc_triage_99"
    assert data["lifecycle_state"] == "HYPOTHESIS_FORMED"
    assert len(data["alerts"]) == 1
    assert len(data["hypotheses"]) == 1


@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_post_hypothesis_endpoint(mock_query):
    """Verify POST /api/incidents/{incident_id}/hypotheses attaches evidence to blackboard."""
    mock_query.return_value = [
        ["hypothesis_id", "status", "attached_count"],
        [["hyp_01", "PROPOSED", 1]]
    ]
    payload = {
        "agent_id": "RCA_Agent",
        "statement": "Missing timeout in stripe client",
        "target_commit_sha": "c3d9a107",
        "initial_confidence": 0.85,
        "evidence_items": [
            {"evidence_type": "METRIC_SPIKE", "source": "Prometheus", "payload": "p99 4850ms", "confidence": 0.95}
        ]
    }
    response = client.post("/api/incidents/inc_triage_99/hypotheses", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["hypothesis_id"] == "hyp_01"
    assert data["status"] == "PROPOSED"
    assert data["attached_count"] == 1


def test_cast_consensus_vote_endpoint():
    """Verify POST /api/incidents/{incident_id}/consensus executes Quorum Consensus."""
    payload = {
        "agent_id": "Memory_Agent",
        "hypothesis_id": "hyp_01",
        "decision": "APPROVE",
        "weight": 0.35,
        "reasoning": "Historical postmortem cosine match 0.94 and verified playbook"
    }
    response = client.post("/api/incidents/inc_triage_99/consensus", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "weighted_consensus_score" in data
    assert "quorum_reached" in data
    assert "status" in data


@patch("backend.api.incidents.db_client.create_sandbox", new_callable=AsyncMock)
@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_simulate_remediation_endpoint(mock_query, mock_sandbox):
    """Verify POST /api/incidents/{incident_id}/remediation/simulate forks ephemeral sandbox."""
    mock_sandbox.return_value = "sandbox_inc_triage_99"
    mock_query.return_value = [
        ["plan_id", "execution_state", "incident_state"],
        [["plan_canary_01", "CANARY_ACTIVE", "REMEDIATING"]]
    ]
    payload = {
        "hypothesis_id": "hyp_01",
        "action_type": "POD_DRAIN",
        "target_entity": "PaymentService",
        "command_payload": "kubectl drain pod/payment-6b8f",
        "rollback_payload": "kubectl uncordon pod/payment-6b8f"
    }
    response = client.post("/api/incidents/inc_triage_99/remediation/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sandbox_id"] == "sandbox_inc_triage_99"
    assert data["execution_state"] == "CANARY_ACTIVE"


def test_chaos_inject_and_scenarios():
    """Verify POST /api/chaos/inject and GET /api/chaos/scenarios."""
    scenarios_resp = client.get("/api/chaos/scenarios")
    assert scenarios_resp.status_code == 200
    assert len(scenarios_resp.json()["scenarios"]) >= 3

    inject_resp = client.post("/api/chaos/inject", json={"scenario": "socket_timeout", "service": "PaymentService"})
    assert inject_resp.status_code == 200
    data = inject_resp.json()
    assert data["status"] == "FAULT_INJECTED"
    assert data["scenario"] == "socket_timeout"
    assert data["service"] == "PaymentService"


def test_cicd_blast_gate_evaluation():
    """Verify POST /api/cicd/blast-gate blocks risky changes touching Tier-1 payment services."""
    payload = {
        "pr_number": 412,
        "repo_url": "https://github.com/company/core",
        "changed_files": ["services/payment/stripe.py"],
        "diff_patch": "- timeout=3.0\n+ timeout=None"
    }
    response = client.post("/api/cicd/blast-gate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["pr_number"] == 412
    assert data["verdict"] == "BLOCKED_BY_POLICY"
    assert data["structural_risk_index"] >= 0.70
    assert "PaymentService" in data["impacted_tier1_services"]


def test_copilot_natural_language_query():
    """Verify POST /api/copilot/query generates safe OpenCypher queries."""
    payload = {"prompt": "Which Tier-1 microservices depend on PaymentService?"}
    response = client.post("/api/copilot/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "DEPENDS_ON" in data["generated_cypher"]
    assert "PaymentService" in data["generated_cypher"]
    assert len(data["results"]) > 0


if __name__ == "__main__":
    tests = [
        ("test_health_check_endpoint", test_health_check_endpoint),
        ("test_triage_incident_endpoint", test_triage_incident_endpoint),
        ("test_get_blackboard_snapshot_endpoint", test_get_blackboard_snapshot_endpoint),
        ("test_post_hypothesis_endpoint", test_post_hypothesis_endpoint),
        ("test_cast_consensus_vote_endpoint", test_cast_consensus_vote_endpoint),
        ("test_simulate_remediation_endpoint", test_simulate_remediation_endpoint),
        ("test_chaos_inject_and_scenarios", test_chaos_inject_and_scenarios),
        ("test_cicd_blast_gate_evaluation", test_cicd_blast_gate_evaluation),
        ("test_copilot_natural_language_query", test_copilot_natural_language_query),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f"Running {name}...")
        try:
            test_fn()
            print(f"PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {name} -> {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\nAPI Router Test Results: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
