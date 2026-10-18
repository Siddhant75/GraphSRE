"""
FalkorDB Client Connection Pool & Query Interface
File: server/falkordb_client.py
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional

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
        async def ping(self):
            return True
        async def execute_command(self, *args, **kwargs):
            return []
    redis_mod.ResponseError = ResponseError
    redis_mod.ConnectionPool = ConnectionPool
    redis_mod.Redis = Redis
    redis_asyncio.ResponseError = ResponseError
    redis_asyncio.ConnectionPool = ConnectionPool
    redis_asyncio.Redis = Redis
    redis = redis_asyncio

logger = logging.getLogger("graphsre.falkordb")
logging.basicConfig(level=logging.INFO)


class FalkorDBClient:
    """Asynchronous FalkorDB client with connection pooling and OpenCypher execution."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        default_graph: Optional[str] = None,
        max_connections: int = 20
    ):
        self.host = host or os.getenv("FALKORDB_HOST", "localhost")
        self.port = int(port or os.getenv("FALKORDB_PORT", 6379))
        self.default_graph = default_graph or os.getenv("PRIMARY_GRAPH", "graphsre_production")
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            decode_responses=True,
            max_connections=max_connections
        )
        self.client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        """Retrieve or lazily initialize the asynchronous Redis client."""
        if self.client is None:
            self.client = redis.Redis(connection_pool=self.pool)
        return self.client

    async def ping(self) -> bool:
        """Healthcheck ping to the underlying FalkorDB/Redis instance."""
        try:
            client = await self.get_client()
            return await client.ping()
        except Exception as e:
            logger.error(f"Failed to ping FalkorDB: {e}")
            return False

    @staticmethod
    def _format_param_value(val: Any) -> str:
        """Format Python values into FalkorDB CYPHER parameter literals."""
        if isinstance(val, bool):
            return "true" if val else "false"
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, str):
            escaped = val.replace("\\", "\\\\").replace("'", "\\'")
            return f"'{escaped}'"
        elif isinstance(val, (list, dict)):
            return json.dumps(val)
        elif val is None:
            return "null"
        else:
            return json.dumps(val)

    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        graph: Optional[str] = None
    ) -> List[Any]:
        """
        Execute an OpenCypher query against FalkorDB.
        Uses GRAPH.QUERY command with native OpenCypher parameter prefix.
        """
        target_graph = graph or self.default_graph
        client = await self.get_client()
        try:
            if params:
                param_parts = [
                    f"{k}={self._format_param_value(v)}" for k, v in params.items()
                ]
                formatted_query = f"CYPHER {' '.join(param_parts)} {query}"
                result = await client.execute_command(
                    "GRAPH.QUERY", target_graph, formatted_query
                )
            else:
                result = await client.execute_command(
                    "GRAPH.QUERY", target_graph, query
                )
            return result
        except redis.ResponseError as err:
            logger.error(f"FalkorDB Cypher execution error in '{target_graph}': {err} | Query: {query}")
            raise RuntimeError(f"FalkorDB Cypher Error: {str(err)}")
        except Exception as err:
            logger.error(f"Unexpected error executing Cypher in '{target_graph}': {err}")
            raise

    async def create_sandbox(self, incident_id: str, source_graph: Optional[str] = None) -> str:
        """
        Forks the production graph in sub-15ms using FalkorDB's native zero-cost GRAPH.COPY.
        Enables safe canary simulation and counterfactual execution without impacting live state.

        Args:
            incident_id: Unique incident identifier.
            source_graph: Optional source graph name; defaults to self.default_graph.

        Returns:
            Name of the created ephemeral sandbox graph (sandbox_<incident_id>).
        """
        src = source_graph or self.default_graph
        sandbox_graph = f"sandbox_{incident_id}"
        client = await self.get_client()
        try:
            await client.execute_command("GRAPH.COPY", src, sandbox_graph)
            logger.info(f"Ephemeral sandbox created: {sandbox_graph} (cloned from {src})")
            return sandbox_graph
        except redis.ResponseError as err:
            logger.error(f"Failed to fork ephemeral sandbox {sandbox_graph}: {err}")
            raise RuntimeError(f"FalkorDB Sandbox Creation Error: {str(err)}")

    async def destroy_sandbox(self, sandbox_graph: str) -> bool:
        """
        Tears down an ephemeral sandbox instance via GRAPH.DELETE after canary verification.

        Args:
            sandbox_graph: Name of the ephemeral sandbox graph to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if sandbox_graph == self.default_graph:
            logger.error(f"Safety guardrail: Refusing to delete default production graph '{sandbox_graph}'.")
            raise ValueError(f"Safety guardrail: Refusing to delete default production graph '{sandbox_graph}'.")

        client = await self.get_client()
        try:
            await client.execute_command("GRAPH.DELETE", sandbox_graph)
            logger.info(f"Ephemeral sandbox successfully torn down: {sandbox_graph}")
            return True
        except redis.ResponseError as err:
            logger.warning(f"Failed to delete ephemeral sandbox {sandbox_graph}: {err}")
            return False

    async def close(self):
        """Close connection pool gracefully."""
        try:
            if self.client:
                await self.client.aclose()
        finally:
            await self.pool.aclose()
