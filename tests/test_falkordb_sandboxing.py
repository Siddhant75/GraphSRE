import os
import sys
from unittest.mock import AsyncMock

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
        class raises:
            def __init__(self, expected_exc):
                self.expected_exc = expected_exc
                self.value = None
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    raise AssertionError(f"Expected {self.expected_exc.__name__} but no exception was raised.")
                if not issubclass(exc_type, self.expected_exc):
                    return False
                self.value = exc_val
                return True
    pytest = _PytestMock()

try:
    import redis.asyncio as redis
except ImportError:
    import types
    redis_mod = types.ModuleType("redis")
    redis_asyncio = types.ModuleType("redis.asyncio")
    class ResponseError(Exception):
        pass
    class ConnectionPool:
        def __init__(self, *args, **kwargs):
            pass
        async def aclose(self):
            pass
    class Redis:
        def __init__(self, *args, **kwargs):
            pass
        async def aclose(self):
            pass
    redis_mod.ResponseError = ResponseError
    redis_mod.ConnectionPool = ConnectionPool
    redis_mod.Redis = Redis
    redis_asyncio.ResponseError = ResponseError
    redis_asyncio.ConnectionPool = ConnectionPool
    redis_asyncio.Redis = Redis
    sys.modules["redis"] = redis_mod
    sys.modules["redis.asyncio"] = redis_asyncio
    redis = redis_asyncio

from server.falkordb_client import FalkorDBClient


@pytest.mark.asyncio
async def test_create_sandbox_invokes_graph_copy():
    """Verify create_sandbox executes native FalkorDB GRAPH.COPY command."""
    client = FalkorDBClient(default_graph="prod_graph")
    mock_redis = AsyncMock()
    mock_redis.execute_command.return_value = "OK"
    client.client = mock_redis

    sandbox_name = await client.create_sandbox("inc_001")
    assert sandbox_name == "sandbox_inc_001"
    mock_redis.execute_command.assert_called_once_with(
        "GRAPH.COPY", "prod_graph", "sandbox_inc_001"
    )


@pytest.mark.asyncio
async def test_create_sandbox_with_custom_source():
    """Verify create_sandbox accepts custom source graph."""
    client = FalkorDBClient(default_graph="prod_graph")
    mock_redis = AsyncMock()
    mock_redis.execute_command.return_value = "OK"
    client.client = mock_redis

    sandbox_name = await client.create_sandbox("inc_002", source_graph="staging_graph")
    assert sandbox_name == "sandbox_inc_002"
    mock_redis.execute_command.assert_called_once_with(
        "GRAPH.COPY", "staging_graph", "sandbox_inc_002"
    )


@pytest.mark.asyncio
async def test_create_sandbox_error_raises_runtime_error():
    """Verify failure during GRAPH.COPY raises RuntimeError."""
    client = FalkorDBClient()
    mock_redis = AsyncMock()
    mock_redis.execute_command.side_effect = redis.ResponseError("Graph not found")
    client.client = mock_redis

    with pytest.raises(RuntimeError) as exc:
        await client.create_sandbox("inc_fail")
    assert "FalkorDB Sandbox Creation Error" in str(exc.value)


@pytest.mark.asyncio
async def test_destroy_sandbox_invokes_graph_delete():
    """Verify destroy_sandbox executes native FalkorDB GRAPH.DELETE command."""
    client = FalkorDBClient()
    mock_redis = AsyncMock()
    mock_redis.execute_command.return_value = "OK"
    client.client = mock_redis

    success = await client.destroy_sandbox("sandbox_inc_001")
    assert success is True
    mock_redis.execute_command.assert_called_once_with(
        "GRAPH.DELETE", "sandbox_inc_001"
    )


@pytest.mark.asyncio
async def test_destroy_sandbox_handles_error_gracefully():
    """Verify destroy_sandbox returns False instead of crashing if graph does not exist."""
    client = FalkorDBClient()
    mock_redis = AsyncMock()
    mock_redis.execute_command.side_effect = redis.ResponseError("Graph not found")
    client.client = mock_redis

    success = await client.destroy_sandbox("nonexistent_sandbox")
    assert success is False


@pytest.mark.asyncio
async def test_destroy_sandbox_guardrail_prevents_deleting_default_graph():
    """Verify destroy_sandbox raises ValueError if attempting to delete the default graph."""
    client = FalkorDBClient(default_graph="graphsre_production")
    with pytest.raises(ValueError) as exc:
        await client.destroy_sandbox("graphsre_production")
    assert "Safety guardrail" in str(exc.value)


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

    print("Running test_create_sandbox_invokes_graph_copy...")
    run_coroutine(test_create_sandbox_invokes_graph_copy())
    print("PASS: test_create_sandbox_invokes_graph_copy")

    print("Running test_create_sandbox_with_custom_source...")
    run_coroutine(test_create_sandbox_with_custom_source())
    print("PASS: test_create_sandbox_with_custom_source")

    print("Running test_create_sandbox_error_raises_runtime_error...")
    run_coroutine(test_create_sandbox_error_raises_runtime_error())
    print("PASS: test_create_sandbox_error_raises_runtime_error")

    print("Running test_destroy_sandbox_invokes_graph_delete...")
    run_coroutine(test_destroy_sandbox_invokes_graph_delete())
    print("PASS: test_destroy_sandbox_invokes_graph_delete")

    print("Running test_destroy_sandbox_handles_error_gracefully...")
    run_coroutine(test_destroy_sandbox_handles_error_gracefully())
    print("PASS: test_destroy_sandbox_handles_error_gracefully")

    print("Running test_destroy_sandbox_guardrail_prevents_deleting_default_graph...")
    run_coroutine(test_destroy_sandbox_guardrail_prevents_deleting_default_graph())
    print("PASS: test_destroy_sandbox_guardrail_prevents_deleting_default_graph")

    print("\nAll 6 sandboxing tests passed successfully!")
