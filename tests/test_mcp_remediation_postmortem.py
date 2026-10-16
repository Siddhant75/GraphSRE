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
    graphsre_execute_remediation_step,
    graphsre_commit_postmortem,
    decay_stale_shortcut_edges,
    prune_obsolete_shortcut_edges,
)


@pytest.mark.asyncio
async def test_remediation_dry_run_creates_sandbox():
    """Verify dry_run=True invokes FalkorDB GRAPH.COPY ephemeral sandbox before executing mutation."""
    mock_plan_res = [
        ["plan_id", "execution_state", "incident_state"],
        [["plan_canary_01", "CANARY_ACTIVE", "REMEDIATING"]]
    ]
    with patch("server.mcp_server.db_client.create_sandbox", new_callable=AsyncMock) as mock_sandbox, \
         patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:

        mock_sandbox.return_value = "sandbox_inc_8f3a12"
        mock_exec.return_value = mock_plan_res

        result = await graphsre_execute_remediation_step(
            incident_id="inc_8f3a12",
            hypothesis_id="hyp_99b1",
            action_type="GIT_REVERT_PR",
            target_entity="PaymentService",
            command_payload="git revert c3d9a107 --no-edit",
            rollback_payload="git reset --hard HEAD~1",
            dry_run=True,
        )

        mock_sandbox.assert_called_once_with("inc_8f3a12")
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert kwargs.get("graph") == "sandbox_inc_8f3a12"
        params = args[1]
        assert params["incident_id"] == "inc_8f3a12"
        assert params["hypothesis_id"] == "hyp_99b1"
        assert params["action_type"] == "GIT_REVERT_PR"
        assert params["target_entity"] == "PaymentService"
        assert params["command_payload"] == "git revert c3d9a107 --no-edit"
        assert params["rollback_payload"] == "git reset --hard HEAD~1"

        assert result["dry_run"] is True
        assert result["sandbox_id"] == "sandbox_inc_8f3a12"
        assert result["plan_id"] == "plan_canary_01"
        assert result["execution_state"] == "CANARY_ACTIVE"
        assert result["incident_state"] == "REMEDIATING"


@pytest.mark.asyncio
async def test_remediation_live_run_executes_on_primary_graph():
    """Verify dry_run=False does not invoke create_sandbox and executes on default/primary graph."""
    mock_plan_res = [
        ["plan_id", "execution_state", "incident_state"],
        [["plan_live_99", "CANARY_ACTIVE", "REMEDIATING"]]
    ]
    with patch("server.mcp_server.db_client.create_sandbox", new_callable=AsyncMock) as mock_sandbox, \
         patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:

        mock_exec.return_value = mock_plan_res

        result = await graphsre_execute_remediation_step(
            incident_id="inc_8f3a12",
            hypothesis_id="hyp_99b1",
            action_type="ROLLBACK_DEPLOYMENT",
            target_entity="PaymentService",
            command_payload="kubectl rollout undo deployment/payment",
            rollback_payload="kubectl rollout undo deployment/payment",
            dry_run=False,
        )

        mock_sandbox.assert_not_called()
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert kwargs.get("graph") is None

        assert result["dry_run"] is False
        assert result["sandbox_id"] is None
        assert result["plan_id"] == "plan_live_99"
        assert result["execution_state"] == "CANARY_ACTIVE"
        assert result["incident_state"] == "REMEDIATING"


@pytest.mark.asyncio
async def test_commit_postmortem_shortcut_edge_synthesis():
    """Verify committing postmortem writes vector embedding, resolves incident, and synthesizes [:CAUSED_BY_SHORTCUT] edge."""
    mock_postmortem_res = [
        ["postmortem_id", "final_lifecycle_state", "shortcut_edge_weight"],
        [["postmortem_inc_8f3a12", "RESOLVED", 1.0]]
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_postmortem_res

        dummy_embedding = [0.1] * 384
        res = await graphsre_commit_postmortem(
            incident_id="inc_8f3a12",
            root_cause_summary="Missing HTTP socket read timeout in payment webhook client",
            resolution_summary="Reverted commit c3d9a107 and restored 3s socket read timeout",
            mttr_seconds=184,
            embedding=dummy_embedding,
        )

        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        params = args[1]
        assert params["incident_id"] == "inc_8f3a12"
        assert params["root_cause_summary"] == "Missing HTTP socket read timeout in payment webhook client"
        assert params["resolution_summary"] == "Reverted commit c3d9a107 and restored 3s socket read timeout"
        assert params["mttr_seconds"] == 184
        assert params["embedding"] == dummy_embedding

        assert res["postmortem_id"] == "postmortem_inc_8f3a12"
        assert res["final_lifecycle_state"] == "RESOLVED"
        assert res["shortcut_edge_weight"] == 1.0


@pytest.mark.asyncio
async def test_decay_and_pruning_queries():
    """Verify maintenance routines for continuous edge decay and obsolete shortcut edge pruning."""
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = [["edges_updated"], [[4]]]
        decay_res = await decay_stale_shortcut_edges()
        assert decay_res == 4
        mock_exec.assert_called_once()
        decay_query = mock_exec.call_args[0][0]
        assert "CAUSED_BY_SHORTCUT" in decay_query
        assert "exp(" in decay_query

        mock_exec.reset_mock()
        mock_exec.return_value = [["edges_deleted"], [[1]]]
        prune_res = await prune_obsolete_shortcut_edges()
        assert prune_res == 1
        mock_exec.assert_called_once()
        prune_query = mock_exec.call_args[0][0]
        assert "CAUSED_BY_SHORTCUT" in prune_query
        assert "DELETE" in prune_query


@pytest.mark.asyncio
async def test_commit_postmortem_missing_incident():
    """Verify committing postmortem returns error status when incident is not found."""
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = []

        res = await graphsre_commit_postmortem(
            incident_id="inc_missing_404",
            root_cause_summary="Something broke",
            resolution_summary="Fixed it",
            mttr_seconds=60,
            embedding=[0.0] * 384,
        )

        assert res["status"] == "ERROR"
        assert "inc_missing_404" in res["error"]


@pytest.mark.asyncio
async def test_decay_and_pruning_empty_results():
    """Verify maintenance queries gracefully return 0 on empty results."""
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = []
        decay_res = await decay_stale_shortcut_edges()
        assert decay_res == 0

        prune_res = await prune_obsolete_shortcut_edges()
        assert prune_res == 0


@pytest.mark.asyncio
async def test_remediation_missing_node_returns_error():
    """Verify graphsre_execute_remediation_step returns structured error when incident or hypothesis does not exist."""
    with patch("server.mcp_server.db_client.create_sandbox", new_callable=AsyncMock) as mock_sandbox, \
         patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:

        mock_sandbox.return_value = "sandbox_inc_missing"
        mock_exec.return_value = [["header"], []]

        result = await graphsre_execute_remediation_step(
            incident_id="inc_missing",
            hypothesis_id="hyp_missing",
            action_type="POD_DRAIN",
            target_entity="PaymentService",
            command_payload="kubectl drain node-1",
            rollback_payload="kubectl uncordon node-1",
            dry_run=True,
        )

        assert result["status"] == "ERROR"
        assert "not found" in result["error"]
        assert result["incident_id"] == "inc_missing"
        assert result["hypothesis_id"] == "hyp_missing"
        assert result["dry_run"] is True
        assert result["sandbox_id"] == "sandbox_inc_missing"


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

    print("Running test_remediation_dry_run_creates_sandbox...")
    run_coroutine(test_remediation_dry_run_creates_sandbox())
    print("PASS: test_remediation_dry_run_creates_sandbox")

    print("Running test_remediation_live_run_executes_on_primary_graph...")
    run_coroutine(test_remediation_live_run_executes_on_primary_graph())
    print("PASS: test_remediation_live_run_executes_on_primary_graph")

    print("Running test_commit_postmortem_shortcut_edge_synthesis...")
    run_coroutine(test_commit_postmortem_shortcut_edge_synthesis())
    print("PASS: test_commit_postmortem_shortcut_edge_synthesis")

    print("Running test_decay_and_pruning_queries...")
    run_coroutine(test_decay_and_pruning_queries())
    print("PASS: test_decay_and_pruning_queries")

    print("Running test_commit_postmortem_missing_incident...")
    run_coroutine(test_commit_postmortem_missing_incident())
    print("PASS: test_commit_postmortem_missing_incident")

    print("Running test_decay_and_pruning_empty_results...")
    run_coroutine(test_decay_and_pruning_empty_results())
    print("PASS: test_decay_and_pruning_empty_results")

    print("Running test_remediation_missing_node_returns_error...")
    run_coroutine(test_remediation_missing_node_returns_error())
    print("PASS: test_remediation_missing_node_returns_error")

    print("\nAll 7 MCP remediation and postmortem tests passed successfully!")
