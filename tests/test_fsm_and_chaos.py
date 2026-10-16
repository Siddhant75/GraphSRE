import os
import sys

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    import re

    class _RaisesContext:
        def __init__(self, expected_exception, match=None):
            self.expected_exception = expected_exception
            self.match = match

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(f"Expected exception {self.expected_exception.__name__} was not raised")
            if not issubclass(exc_type, self.expected_exception):
                return False
            if self.match and not re.search(self.match, str(exc_val)):
                raise AssertionError(f"Exception message '{exc_val}' does not match pattern '{self.match}'")
            return True

    class _PytestMock:
        @staticmethod
        def approx(expected, rel=None, abs=None):
            import builtins
            class _Approx:
                def __init__(self, val, tol=1e-3):
                    self.val = val
                    self.tol = tol

                def __eq__(self, other):
                    diff = builtins.abs(self.val - other)
                    return diff <= self.tol

            tol = rel if rel is not None else (abs if abs is not None else 1e-3)
            return _Approx(expected, tol)

        @staticmethod
        def raises(expected_exception, match=None):
            return _RaisesContext(expected_exception, match=match)

        class mark:
            @staticmethod
            def asyncio(fn):
                return fn

    pytest = _PytestMock()

from backend.fsm.lifecycle import IncidentLifecycleFSM, IncidentState
from backend.fsm.consensus import QuorumConsensusEngine
from backend.chaos.fault_injector import ChaosFaultInjector


def test_fsm_valid_lifecycle_transitions():
    """Verify standard happy path state transitions through incident lifecycle."""
    fsm = IncidentLifecycleFSM("inc_test_01")
    assert fsm.current_state == IncidentState.DETECTED

    fsm.transition(IncidentState.TRIAGED)
    assert fsm.current_state == IncidentState.TRIAGED

    fsm.transition(IncidentState.INVESTIGATING)
    assert fsm.current_state == IncidentState.INVESTIGATING

    fsm.transition(IncidentState.HYPOTHESIS_FORMED)
    assert fsm.current_state == IncidentState.HYPOTHESIS_FORMED

    fsm.transition(IncidentState.CONSENSUS_REACHED)
    assert fsm.current_state == IncidentState.CONSENSUS_REACHED

    fsm.transition(IncidentState.SANDBOX_SIMULATED)
    assert fsm.current_state == IncidentState.SANDBOX_SIMULATED

    fsm.transition(IncidentState.REMEDIATING)
    assert fsm.current_state == IncidentState.REMEDIATING

    fsm.transition(IncidentState.RESOLVED)
    assert fsm.current_state == IncidentState.RESOLVED
    assert fsm.is_terminal() is True


def test_fsm_invalid_lifecycle_transition_raises():
    """Verify that jumping directly from DETECTED to RESOLVED raises ValueError."""
    fsm = IncidentLifecycleFSM("inc_test_02")
    with pytest.raises(ValueError, match="Invalid state transition"):
        fsm.transition(IncidentState.RESOLVED)


def test_quorum_consensus_approval_supermajority():
    """Verify RCA (0.40) + Memory (0.35) APPROVE reaches 0.75 supermajority."""
    votes = [
        {"agent_id": "RCA_Agent", "decision": "APPROVE", "weight": 0.40},
        {"agent_id": "Memory_Agent", "decision": "APPROVE", "weight": 0.35}
    ]
    result = QuorumConsensusEngine.evaluate_quorum(votes)
    assert pytest.approx(result["weighted_consensus_score"], 0.001) == 0.75
    assert result["quorum_reached"] is True
    assert result["status"] == "HYPOTHESIS_VERIFIED"


def test_quorum_consensus_veto_by_memory_agent():
    """
    Verify VETO rule:
    Memory Agent has weight 0.35 >= 0.35. A REJECT vote from Memory Agent halts mitigation
    even if RCA (0.40) and Triage (0.25) approve (total approving score = 0.65).
    """
    votes = [
        {"agent_id": "RCA_Agent", "decision": "APPROVE", "weight": 0.40},
        {"agent_id": "Triage_Agent", "decision": "APPROVE", "weight": 0.25},
        {"agent_id": "Memory_Agent", "decision": "REJECT", "weight": 0.35}
    ]
    result = QuorumConsensusEngine.evaluate_quorum(votes)
    assert result["quorum_reached"] is False
    assert result["has_veto"] is True
    assert result["status"] == "REJECTED_BY_VETO"


def test_quorum_consensus_veto_by_rca_agent():
    """Verify RCA Agent (w = 0.40 >= 0.35) REJECT triggers veto."""
    votes = [
        {"agent_id": "RCA_Agent", "decision": "REJECT", "weight": 0.40},
        {"agent_id": "Memory_Agent", "decision": "APPROVE", "weight": 0.35},
        {"agent_id": "Triage_Agent", "decision": "APPROVE", "weight": 0.25}
    ]
    result = QuorumConsensusEngine.evaluate_quorum(votes)
    assert result["quorum_reached"] is False
    assert result["has_veto"] is True
    assert result["status"] == "REJECTED_BY_VETO"


def test_quorum_consensus_explicit_veto_decision():
    """Verify explicit decision='VETO' triggers veto regardless of weight."""
    votes = [
        {"agent_id": "Triage_Agent", "decision": "VETO", "weight": 0.25}
    ]
    result = QuorumConsensusEngine.evaluate_quorum(votes)
    assert result["has_veto"] is True
    assert result["status"] == "REJECTED_BY_VETO"


def test_chaos_fault_injector_payloads():
    """Verify synthetic fault payloads produced by ChaosFaultInjector."""
    injector = ChaosFaultInjector(webhook_url="http://localhost:8000")

    timeout_fault = injector.create_socket_timeout_payload(service="PaymentService")
    assert timeout_fault["alert_name"] == "PaymentService_SocketReadTimeout"
    assert timeout_fault["metric_value"] == 4850.0
    assert timeout_fault["threshold"] == 500.0

    pool_fault = injector.create_connection_exhaustion_payload(service="PaymentService")
    assert pool_fault["alert_name"] == "PaymentService_DBConnectionPoolExhausted"
    assert pool_fault["metric_value"] == 100.0


if __name__ == "__main__":
    tests = [
        ("test_fsm_valid_lifecycle_transitions", test_fsm_valid_lifecycle_transitions),
        ("test_fsm_invalid_lifecycle_transition_raises", test_fsm_invalid_lifecycle_transition_raises),
        ("test_quorum_consensus_approval_supermajority", test_quorum_consensus_approval_supermajority),
        ("test_quorum_consensus_veto_by_memory_agent", test_quorum_consensus_veto_by_memory_agent),
        ("test_quorum_consensus_veto_by_rca_agent", test_quorum_consensus_veto_by_rca_agent),
        ("test_quorum_consensus_explicit_veto_decision", test_quorum_consensus_explicit_veto_decision),
        ("test_chaos_fault_injector_payloads", test_chaos_fault_injector_payloads),
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

    print(f"\nFSM & Chaos Test Results: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
