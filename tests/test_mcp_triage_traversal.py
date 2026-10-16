import os
import sys
import asyncio
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
    graphsre_triage_alert,
    graphsre_traverse_causal_path,
)


@pytest.mark.asyncio
async def test_graphsre_triage_alert_execution():
    """Verify graphsre_triage_alert invokes FalkorDB OpenCypher query with correct params and returns structured triage."""
    mock_db_result = [
        ["incident_id", "severity", "blast_radius", "impacted_services", "sev_score"],
        [["inc_8f3a12", "SEV_1", 3, ["CheckoutService", "OrderAPI"], 92.5]]
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_db_result

        result = await graphsre_triage_alert(
            alert_id="alt_001",
            fingerprint="fp_sha256_stripe_err",
            alert_name="PaymentService_SocketReadTimeout",
            source="Prometheus",
            target_service="PaymentService",
            metric_value=4850.0,
            threshold=500.0,
            timestamp=1718900000000
        )

        assert result["status"] == "TRIAGED"
        assert result["incident_id"] == "inc_8f3a12"
        assert result["severity"] == "SEV_1"
        assert result["blast_radius"] == 3
        assert "CheckoutService" in result["impacted_services"]
        assert result["sev_score"] == 92.5

        # Verify query parameters passed to FalkorDB
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        params = args[1]
        assert params["target_service"] == "PaymentService"
        assert params["alert_name"] == "PaymentService_SocketReadTimeout"
        assert params["metric_value"] == 4850.0


@pytest.mark.asyncio
async def test_graphsre_traverse_causal_path_execution():
    """Verify graphsre_traverse_causal_path navigates from Service to Endpoint, AST Functions, and Commit."""
    mock_culprits = [
        ["culprit_function", "file_path", "line_start", "line_end", "culprit_commit", "author", "author_slack", "owning_team", "commit_message", "diff_summary", "call_depth"],
        [
            [
                "payment.gateway.process_charge",
                "services/payment/gateway.py",
                42,
                88,
                "c3d9a107",
                "alice@company.io",
                "@alice",
                "Core-Payments",
                "refactor: update payment gateway client",
                "- timeout=3.0\n+ timeout=None",
                2
            ]
        ]
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_culprits

        result = await graphsre_traverse_causal_path(
            incident_id="inc_8f3a12",
            service_name="PaymentService",
            max_depth=4,
            time_window_hours=6
        )

        assert result["incident_id"] == "inc_8f3a12"
        assert len(result["culprits"]) == 1
        culprit = result["culprits"][0]
        assert culprit["culprit_function"] == "payment.gateway.process_charge"
        assert culprit["culprit_commit"] == "c3d9a107"
        assert culprit["author_slack"] == "@alice"
        assert culprit["call_depth"] == 2

        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        params = args[1]
        assert params["incident_id"] == "inc_8f3a12"
        assert params["service_name"] == "PaymentService"
        assert params["max_depth"] == 4
        assert params["time_window_hours"] == 6


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

    print("Running test_graphsre_triage_alert_execution...")
    run_coroutine(test_graphsre_triage_alert_execution())
    print("PASS: test_graphsre_triage_alert_execution")

    print("Running test_graphsre_traverse_causal_path_execution...")
    run_coroutine(test_graphsre_traverse_causal_path_execution())
    print("PASS: test_graphsre_traverse_causal_path_execution")

    print("\nAll MCP triage and traversal tests passed successfully!")

