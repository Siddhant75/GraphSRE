import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

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
async def test_falkordb_client_initialization_defaults():
    """Verify FalkorDBClient initializes connection pool with host, port, and default graph."""
    client = FalkorDBClient(host="localhost", port=6379, default_graph="test_graph")
    assert client.host == "localhost"
    assert client.port == 6379
    assert client.default_graph == "test_graph"
    assert client.pool is not None


@pytest.mark.asyncio
async def test_falkordb_ping_success():
    """Verify ping returns True when Redis ping succeeds."""
    client = FalkorDBClient()
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    client.client = mock_redis

    is_alive = await client.ping()
    assert is_alive is True
    mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_falkordb_ping_failure():
    """Verify ping returns False when connection raises an exception."""
    client = FalkorDBClient()
    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = ConnectionError("Connection refused")
    client.client = mock_redis

    is_alive = await client.ping()
    assert is_alive is False


@pytest.mark.asyncio
async def test_execute_query_without_params():
    """Verify GRAPH.QUERY execution without parameters."""
    client = FalkorDBClient(default_graph="graphsre_prod")
    mock_redis = AsyncMock()
    mock_redis.execute_command.return_value = [["Header"], [["ServiceA"]]]
    client.client = mock_redis

    query = "MATCH (s:Service) RETURN s.name"
    result = await client.execute_query(query)
    assert result == [["Header"], [["ServiceA"]]]
    mock_redis.execute_command.assert_called_once_with("GRAPH.QUERY", "graphsre_prod", query)


@pytest.mark.asyncio
async def test_execute_query_with_params():
    """Verify GRAPH.QUERY execution with formatted parameters string."""
    client = FalkorDBClient(default_graph="graphsre_prod")
    mock_redis = AsyncMock()
    mock_redis.execute_command.return_value = [["Header"], [["PaymentService"]]]
    client.client = mock_redis

    query = "MATCH (s:Service {name: $svc}) RETURN s.name"
    params = {"svc": "PaymentService"}
    result = await client.execute_query(query, params=params)
    expected_query = "CYPHER svc='PaymentService' MATCH (s:Service {name: $svc}) RETURN s.name"
    mock_redis.execute_command.assert_called_once_with(
        "GRAPH.QUERY", "graphsre_prod", expected_query
    )

    # Test types formatting: string with quote, int, float, bool, list, dict
    mock_redis.reset_mock()
    mock_redis.execute_command.return_value = [["Header"], [[1]]]
    complex_params = {
        "text": "O'Reilly",
        "num": 42,
        "ratio": 3.14,
        "is_active": True,
        "tags": ["prod", "critical"],
        "metadata": {"source": "alert_mgr"}
    }
    await client.execute_query("RETURN 1", params=complex_params)
    called_query = mock_redis.execute_command.call_args[0][2]
    assert "text='O\\'Reilly'" in called_query
    assert "num=42" in called_query
    assert "ratio=3.14" in called_query
    assert "is_active=true" in called_query
    assert 'tags=["prod", "critical"]' in called_query
    assert 'metadata={"source": "alert_mgr"}' in called_query
    assert called_query.startswith("CYPHER ")
    assert called_query.endswith("RETURN 1")


@pytest.mark.asyncio
async def test_execute_query_error_handling():
    """Verify redis.ResponseError is caught and re-raised as RuntimeError."""
    client = FalkorDBClient()
    mock_redis = AsyncMock()
    mock_redis.execute_command.side_effect = redis.ResponseError("Syntax error in Cypher query")
    client.client = mock_redis

    with pytest.raises(RuntimeError) as exc_info:
        await client.execute_query("INVALID CYPHER")
    assert "FalkorDB Cypher Error" in str(exc_info.value)


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

    print("Running test_falkordb_client_initialization_defaults...")
    run_coroutine(test_falkordb_client_initialization_defaults())
    print("PASS: test_falkordb_client_initialization_defaults")

    print("Running test_falkordb_ping_success...")
    run_coroutine(test_falkordb_ping_success())
    print("PASS: test_falkordb_ping_success")

    print("Running test_falkordb_ping_failure...")
    run_coroutine(test_falkordb_ping_failure())
    print("PASS: test_falkordb_ping_failure")

    print("Running test_execute_query_without_params...")
    run_coroutine(test_execute_query_without_params())
    print("PASS: test_execute_query_without_params")

    print("Running test_execute_query_with_params...")
    run_coroutine(test_execute_query_with_params())
    print("PASS: test_execute_query_with_params")

    print("Running test_execute_query_error_handling...")
    run_coroutine(test_execute_query_error_handling())
    print("PASS: test_execute_query_error_handling")

    print("\nAll 6 tests passed successfully!")
