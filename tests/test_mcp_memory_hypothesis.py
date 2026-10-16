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

from server.mcp_server import (
    graphsre_query_memory,
    graphsre_post_hypothesis,
    graphsre_get_blackboard_state,
)


@pytest.mark.asyncio
async def test_graphsre_query_memory():
    """Verify hybrid retrieval executing HNSW vector query and calculating Composite Confidence C_SRE."""
    mock_results = [
        [
            "prior_incident_id",
            "past_summary",
            "past_resolution",
            "episodic_sim",
            "suggested_runbook_id",
            "playbook_title",
            "composite_confidence",
        ],
        [
            [
                "postmortem_inc_prev_41",
                "Socket timeout stripped in payment gateway",
                "Reverted commit and reinstated 3s timeout",
                0.94,
                "rb_payment_timeout",
                "Payment Gateway Timeout Playbook",
                0.915,
            ]
        ],
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_results

        dummy_vector = [0.05] * 384
        result = await graphsre_query_memory(
            incident_id="inc_8f3a12",
            hypothesis_id="hyp_001",
            service_name="PaymentService",
            query_vector=dummy_vector,
            metric_snr=0.90,
            top_k=3,
        )

        assert result["incident_id"] == "inc_8f3a12"
        assert result["hypothesis_id"] == "hyp_001"
        assert len(result["matches"]) == 1
        m = result["matches"][0]
        assert m["prior_incident_id"] == "postmortem_inc_prev_41"
        assert m["past_summary"] == "Socket timeout stripped in payment gateway"
        assert m["past_resolution"] == "Reverted commit and reinstated 3s timeout"
        assert m["episodic_sim"] == 0.94
        assert m["suggested_runbook_id"] == "rb_payment_timeout"
        assert m["playbook_title"] == "Payment Gateway Timeout Playbook"
        assert m["composite_confidence"] == 0.915

        # Verify execute_query parameters
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        params = args[1]
        assert params["incident_id"] == "inc_8f3a12"
        assert params["hypothesis_id"] == "hyp_001"
        assert params["service_name"] == "PaymentService"
        assert params["query_vector"] == dummy_vector
        assert params["metric_snr"] == 0.90
        assert params["top_k"] == 3


@pytest.mark.asyncio
async def test_graphsre_post_hypothesis():
    """Verify posting a hypothesis attaches evidence nodes and transitions incident state to HYPOTHESIS_FORMED."""
    mock_post_res = [
        ["hypothesis_id", "status", "attached_count"],
        [["hyp_99b1", "PROPOSED", 2]],
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_post_res

        evidence = [
            {
                "evidence_type": "METRIC_SPIKE",
                "source": "Prometheus",
                "payload": "Latency p99 4850ms",
                "confidence": 0.95,
            },
            {
                "evidence_type": "AST_DIFF",
                "source": "git diff",
                "payload": "- timeout=3.0\n+ timeout=None",
                "confidence": 0.98,
            },
        ]

        res = await graphsre_post_hypothesis(
            incident_id="inc_8f3a12",
            agent_id="RCA_Agent",
            statement="Stripped timeout in payment client causes socket thread starvation",
            target_commit_sha="c3d9a107",
            initial_confidence=0.88,
            evidence_items=evidence,
        )

        assert res["hypothesis_id"] == "hyp_99b1"
        assert res["status"] == "PROPOSED"
        assert res["attached_count"] == 2

        # Verify execute_query parameters
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        params = args[1]
        assert params["incident_id"] == "inc_8f3a12"
        assert params["agent_id"] == "RCA_Agent"
        assert params["statement"] == "Stripped timeout in payment client causes socket thread starvation"
        assert params["target_commit_sha"] == "c3d9a107"
        assert params["initial_confidence"] == 0.88
        assert params["evidence_items"] == evidence


@pytest.mark.asyncio
async def test_graphsre_get_blackboard_state():
    """Verify retrieving complete incident blackboard snapshot."""
    mock_snapshot = [
        ["incident_id", "lifecycle_state", "severity", "blast_radius", "started_at", "alerts", "hypotheses"],
        [
            [
                "inc_8f3a12",
                "HYPOTHESIS_FORMED",
                "SEV_1",
                3,
                1718900000000,
                [{"name": "PaymentService_SocketReadTimeout", "metric_value": 4850.0}],
                [{"hypothesis_id": "hyp_99b1", "statement": "Timeout stripped", "confidence": 0.915}],
            ]
        ],
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_snapshot

        bb = await graphsre_get_blackboard_state("inc_8f3a12")
        assert bb["incident_id"] == "inc_8f3a12"
        assert bb["lifecycle_state"] == "HYPOTHESIS_FORMED"
        assert bb["severity"] == "SEV_1"
        assert bb["blast_radius"] == 3
        assert bb["started_at"] == 1718900000000
        assert len(bb["alerts"]) == 1
        assert len(bb["hypotheses"]) == 1

        # Verify execute_query parameters
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        params = args[1]
        assert params["incident_id"] == "inc_8f3a12"


@pytest.mark.asyncio
async def test_graphsre_query_memory_empty_results():
    """Verify graceful handling when no past incidents match (returns matches: [])."""
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = [["header"], []]

        result = await graphsre_query_memory(
            incident_id="inc_empty",
            hypothesis_id="hyp_none",
            service_name="UnknownService",
            query_vector=[0.0] * 384,
            metric_snr=0.5,
            top_k=3,
        )

        assert result["incident_id"] == "inc_empty"
        assert result["hypothesis_id"] == "hyp_none"
        assert result["matches"] == []


if __name__ == "__main__":
    def run_coroutine(coro):
        """Drive coroutine chain directly without blocking on Windows sandbox loopback pipes."""
        stack = [coro]
        val = None
        exc = None
        while stack:
            current = stack[-1]
            try:
                if exc is not None:
                    to_raise = exc
                    exc = None
                    nxt = current.throw(to_raise)
                else:
                    nxt = current.send(val)
                val = None
                if hasattr(nxt, "send"):
                    stack.append(nxt)
                else:
                    val = nxt
            except StopIteration as si:
                val = si.value
                stack.pop()
            except Exception as e:
                exc = e
                stack.pop()
        if exc is not None:
            raise exc
        return val

    print("Running test_graphsre_query_memory...")
    run_coroutine(test_graphsre_query_memory())
    print("PASS: test_graphsre_query_memory")

    print("Running test_graphsre_post_hypothesis...")
    run_coroutine(test_graphsre_post_hypothesis())
    print("PASS: test_graphsre_post_hypothesis")

    print("Running test_graphsre_get_blackboard_state...")
    run_coroutine(test_graphsre_get_blackboard_state())
    print("PASS: test_graphsre_get_blackboard_state")

    print("Running test_graphsre_query_memory_empty_results...")
    run_coroutine(test_graphsre_query_memory_empty_results())
    print("PASS: test_graphsre_query_memory_empty_results")

    print("\nAll 4 MCP memory and hypothesis tests passed successfully!")
