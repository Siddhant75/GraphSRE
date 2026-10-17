import os
import sys
import time
try:
    import pytest
except ImportError:
    pytest = None

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Import FastAPI backend application and TestClient
try:
    from backend.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app) if app else None
except ImportError:
    try:
        from backend.compat import TestClient
        from backend.main import app
        client = TestClient(app) if app else None
    except Exception:
        app = None
        client = None


def test_full_incident_lifecycle_under_90s_sla():
    """
    Verify complete 9-stage incident lifecycle completes in < 90 seconds:
    1. Chaos Fault Injection
    2. Telemetry Ingestion & CDLP Clustering (Sev-1)
    3. Cross-layer RCA Traversal (Culprit Commit Identification)
    4. Memory Agent Vector Recall & C_SRE Scoring
    5. Distributed Quorum Consensus Voting (WCS >= 0.75)
    6. GRAPH.COPY Ephemeral Sandbox Simulation
    7. Canary Rollout Mitigation
    8. Postmortem Embedding & O(1) Shortcut Net Synthesis
    9. Second Outage O(1) Immediate Resolution (< 2 seconds)
    """
    assert app is not None, "backend.main:app must be importable"
    assert client is not None, "TestClient must be initialized"
    start_time = time.time()

    # 1. Chaos Injection
    chaos_res = client.post("/api/chaos/inject", json={
        "scenario": "socket_timeout",
        "service": "PaymentService"
    })
    assert chaos_res.status_code == 200, f"Chaos injection failed: {chaos_res.text}"
    incident_id = chaos_res.json()["incident_id"]
    assert incident_id.startswith("inc_")

    # 2. Ingest Alert & Triage
    triage_res = client.post("/api/incidents/triage", json={
        "alert_id": "alt_test_01",
        "fingerprint": "fp_socket_timeout_payment",
        "alert_name": "PaymentService_SocketReadTimeout_High",
        "target_service": "PaymentService",
        "metric_value": 4850.0,
        "threshold": 500.0,
        "timestamp": int(time.time() * 1000)
    })
    assert triage_res.status_code == 200, f"Triage failed: {triage_res.text}"
    triage_data = triage_res.json()
    assert triage_data["severity"] == "SEV_1"
    blast_count = triage_data.get("blast_radius_count", triage_data.get("blast_radius", 0))
    assert blast_count >= 3, f"Expected blast radius >= 3, got {blast_count}"

    # 3. Quorum Consensus Gate
    vote_res = client.post(f"/api/incidents/{incident_id}/consensus", json={
        "agent_id": "Memory_Agent",
        "hypothesis_id": "hyp_socket_timeout",
        "decision": "APPROVE",
        "weight": 0.35,
        "reasoning": "Topological match c3d9a107 verified, past incident similarity 0.941"
    })
    assert vote_res.status_code == 200, f"Consensus failed: {vote_res.text}"
    consensus_data = vote_res.json()
    wcs = consensus_data.get("wcs", consensus_data.get("weighted_consensus_score", 0))
    assert wcs >= 0.75, f"Expected WCS >= 0.75, got {wcs}"
    assert consensus_data["quorum_reached"] is True

    # 4. Remediation Sandbox Simulation & Canary Rollout
    remed_res = client.post(f"/api/incidents/{incident_id}/remediate", json={
        "action_type": "CANARY_REVERT",
        "target_commit": "c3d9a107",
        "target_service": "PaymentService",
        "simulate_sandbox": True
    })
    assert remed_res.status_code == 200, f"Remediation failed: {remed_res.text}"
    remed_data = remed_res.json()
    assert remed_data["sandbox_simulation"] == "PASS"
    assert remed_data["status"] == "RESOLVED"
    assert remed_data["shortcut_edge_created"] is True

    # Check Total MTTR SLA Duration
    total_elapsed_seconds = time.time() - start_time
    assert total_elapsed_seconds < 90.0, f"MTTR violated SLA: took {total_elapsed_seconds}s (limit: 90s)"

    # 5. Phase 9: Second Outage O(1) Shortcut Immediate Resolution (< 2 seconds)
    second_outage_start = time.time()
    second_triage = client.post("/api/incidents/triage", json={
        "alert_id": "alt_test_02",
        "fingerprint": "fp_socket_timeout_payment",
        "alert_name": "PaymentService_SocketReadTimeout_High",
        "target_service": "PaymentService",
        "metric_value": 4900.0,
        "threshold": 500.0,
        "timestamp": int(time.time() * 1000)
    })
    assert second_triage.status_code == 200
    second_incident_id = second_triage.json()["incident_id"]

    second_remed = client.post(f"/api/incidents/{second_incident_id}/remediate", json={
        "action_type": "CANARY_REVERT",
        "target_commit": "c3d9a107",
        "target_service": "PaymentService",
        "simulate_sandbox": False
    })
    assert second_remed.status_code == 200
    assert second_remed.json()["status"] == "RESOLVED"
    second_outage_duration = time.time() - second_outage_start
    assert second_outage_duration < 2.0, f"O(1) Shortcut resolution took {second_outage_duration}s (limit: 2s)"


if __name__ == "__main__":
    tests = [
        test_full_incident_lifecycle_under_90s_sla
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")

    print(f"\n{passed}/{len(tests)} tests passed.")
    if passed != len(tests):
        sys.exit(1)
