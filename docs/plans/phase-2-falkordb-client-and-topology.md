# Phase 2: FalkorDB Client, Ephemeral Sandboxing & Topology Seeding Implementation Plan

> **For AI Assistant:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task.

**Goal:** Implement the asynchronous FalkorDB client with connection pooling, native zero-cost ephemeral graph sandboxing (`GRAPH.COPY` and `GRAPH.DELETE`), and the realistic polyglot microservice AST, Git commit, and 384-dimensional vector memory seeding engine.

**Architecture:** Uses `redis.asyncio` connection pooling for sub-millisecond OpenCypher queries against FalkorDB. Employs FalkorDB's native `GRAPH.COPY` command to create instant (<15ms) isolated sandbox graphs for counterfactual canary simulation without mutating production graph state, and seeds realistic microservices, tree-sitter AST nodes, Git commit diffs, and HNSW vector-indexed postmortems.

**Tech Stack:** Python 3.11+, redis.asyncio, FalkorDB OpenCypher, NumPy (L2 normalization), pytest, pytest-asyncio.

---

## Task Breakdown

### Task 2.1: FalkorDB Client & Connection Pooling (`server/falkordb_client.py`)

**Files:**
- Create: `server/falkordb_client.py`
- Test: `tests/test_falkordb_client.py`

**Step 1: Write the failing test**

Create `tests/test_falkordb_client.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from server.falkordb_client import FalkorDBClient
import redis.asyncio as redis

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
    assert result == [["Header"], [["PaymentService"]]]
    mock_redis.execute_command.assert_called_once_with(
        "GRAPH.QUERY", "graphsre_prod", query, "--params", str(params)
    )

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
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_falkordb_client.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'server.falkordb_client'` or missing methods.

**Step 3: Write minimal implementation**

Create `server/falkordb_client.py`:
```python
"""
FalkorDB Client Connection Pool & Query Interface
File: server/falkordb_client.py
"""
import os
import logging
from typing import Any, Dict, List, Optional
import redis.asyncio as redis

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

    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        graph: Optional[str] = None
    ) -> List[Any]:
        """
        Execute an OpenCypher query against FalkorDB.
        Uses GRAPH.QUERY command with optional parameters.
        """
        target_graph = graph or self.default_graph
        client = await self.get_client()
        try:
            if params:
                result = await client.execute_command(
                    "GRAPH.QUERY", target_graph, query, "--params", str(params)
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

    async def close(self):
        """Close connection pool gracefully."""
        if self.client:
            await self.client.aclose()
        await self.pool.aclose()
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_falkordb_client.py -v
```
Expected: PASS (all 6 tests passed).

**Step 5: Commit**

```bash
git add server/falkordb_client.py tests/test_falkordb_client.py
git commit -m "feat(falkordb): implement async falkordb client with connection pool and error handling"
```

---

### Task 2.2: Native Ephemeral Sandboxing Harness (`create_sandbox` via `GRAPH.COPY` and `destroy_sandbox` via `GRAPH.DELETE`)

**Files:**
- Modify: `server/falkordb_client.py`
- Test: `tests/test_falkordb_sandboxing.py`

**Step 1: Write the failing test**

Create `tests/test_falkordb_sandboxing.py`:
```python
import pytest
from unittest.mock import AsyncMock
from server.falkordb_client import FalkorDBClient
import redis.asyncio as redis

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
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_falkordb_sandboxing.py -v
```
Expected: FAIL with `AttributeError: 'FalkorDBClient' object has no attribute 'create_sandbox'`.

**Step 3: Write minimal implementation**

Modify `server/falkordb_client.py` to add `create_sandbox` and `destroy_sandbox` methods:

```python
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
        client = await self.get_client()
        try:
            await client.execute_command("GRAPH.DELETE", sandbox_graph)
            logger.info(f"Ephemeral sandbox successfully torn down: {sandbox_graph}")
            return True
        except redis.ResponseError as err:
            logger.warning(f"Failed to delete ephemeral sandbox {sandbox_graph}: {err}")
            return False
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_falkordb_sandboxing.py -v
```
Expected: PASS (all 5 tests passed).

**Step 5: Commit**

```bash
git add server/falkordb_client.py tests/test_falkordb_sandboxing.py
git commit -m "feat(sandbox): implement native falkordb GRAPH.COPY and GRAPH.DELETE ephemeral sandboxing"
```

---

### Task 2.3: Synthetic Microservice Topology, AST Call Graph & Vector Seeder (`scripts/seed_mock_topology.py`)

**Files:**
- Create: `scripts/seed_mock_topology.py`
- Test: `tests/test_seed_topology.py`

**Step 1: Write the failing test**

Create `tests/test_seed_topology.py`:
```python
import pytest
from scripts.seed_mock_topology import generate_normalized_embedding, get_seed_cypher

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
        "AuthService"
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
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_seed_topology.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.seed_mock_topology'`.

**Step 3: Write minimal implementation**

Create `scripts/seed_mock_topology.py`:
```python
"""
Realistic Microservice Graph, AST Topology & Vector Memory Seeder
File: scripts/seed_mock_topology.py
"""
import os
import sys
from typing import List
import redis
import numpy as np

def generate_normalized_embedding(dim: int = 384) -> List[float]:
    """
    Generate an L2-normalized random unit vector of dimension `dim` (compatible with MiniLM 384-dim).
    """
    vec = np.random.randn(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.tolist()
    return (vec / norm).tolist()

def get_seed_cypher() -> str:
    """
    Returns the OpenCypher DDL and DML to seed:
    1. 6 Polyglot microservices with PageRank and tier attributes.
    2. Inter-service HTTP and gRPC DEPENDS_ON edges with latency timeouts.
    3. API Endpoints exposed by microservices.
    4. Tree-sitter AST Function call hierarchy (:CALLS*).
    5. Suspect Git Commit modifying the critical path.
    6. Engineering teams, on-call engineers, and ownership links.
    7. Standard Operating Procedure (SOP) Runbooks.
    """
    return """
    // 1. Create Polyglot Microservices
    CREATE (frontend:Service {id: 'svc_frontend', name: 'FrontendAPI', tier: 'TIER_1', health_status: 'HEALTHY', p99_latency_ms: 45, error_rate: 0.001, pagerank: 0.85})
    CREATE (checkout:Service {id: 'svc_checkout', name: 'CheckoutService', tier: 'TIER_1', health_status: 'HEALTHY', p99_latency_ms: 120, error_rate: 0.002, pagerank: 0.78})
    CREATE (payment:Service {id: 'svc_payment', name: 'PaymentService', tier: 'TIER_1', health_status: 'HEALTHY', p99_latency_ms: 180, error_rate: 0.005, pagerank: 0.92})
    CREATE (inventory:Service {id: 'svc_inventory', name: 'InventoryService', tier: 'TIER_2', health_status: 'HEALTHY', p99_latency_ms: 60, error_rate: 0.001, pagerank: 0.45})
    CREATE (notification:Service {id: 'svc_notification', name: 'NotificationService', tier: 'TIER_3', health_status: 'HEALTHY', p99_latency_ms: 30, error_rate: 0.000, pagerank: 0.30})
    CREATE (auth:Service {id: 'svc_auth', name: 'AuthService', tier: 'TIER_1', health_status: 'HEALTHY', p99_latency_ms: 25, error_rate: 0.001, pagerank: 0.88})

    // 2. Create Service Dependency Topology
    CREATE (frontend)-[:DEPENDS_ON {protocol: 'HTTP', timeout_ms: 500}]->(checkout)
    CREATE (frontend)-[:DEPENDS_ON {protocol: 'HTTP', timeout_ms: 250}]->(auth)
    CREATE (checkout)-[:DEPENDS_ON {protocol: 'gRPC', timeout_ms: 400}]->(payment)
    CREATE (checkout)-[:DEPENDS_ON {protocol: 'gRPC', timeout_ms: 300}]->(inventory)
    CREATE (payment)-[:DEPENDS_ON {protocol: 'HTTP', timeout_ms: 1000}]->(notification)
    CREATE (payment)-[:DEPENDS_ON {protocol: 'gRPC', timeout_ms: 200}]->(auth)

    // 3. Create API Endpoints
    CREATE (ep_pay:Endpoint {id: 'ep_pay', path: '/api/v1/charge', method: 'POST', protocol: 'HTTP/1.1', sla_p99_ms: 300})
    CREATE (ep_check:Endpoint {id: 'ep_check', path: '/api/v1/checkout', method: 'POST', protocol: 'HTTP/1.1', sla_p99_ms: 500})
    CREATE (payment)-[:EXPOSES]->(ep_pay)
    CREATE (checkout)-[:EXPOSES]->(ep_check)

    // 4. Create Tree-sitter AST Function Call Hierarchy
    CREATE (fn_root:Function {id: 'fn_charge_root', qualified_name: 'payment.gateway.process_charge', file_path: 'services/payment/gateway.py', line_start: 45, line_end: 80, ast_hash: 'h1a9'})
    CREATE (fn_auth:Function {id: 'fn_auth_verify', qualified_name: 'payment.auth.verify_token', file_path: 'services/payment/auth.py', line_start: 10, line_end: 28, ast_hash: 'a2b3'})
    CREATE (fn_webhook:Function {id: 'fn_webhook', qualified_name: 'payment.stripe.call_webhook', file_path: 'services/payment/stripe.py', line_start: 12, line_end: 38, ast_hash: 'w8d2'})
    CREATE (fn_lock:Function {id: 'fn_lock', qualified_name: 'payment.db.acquire_db_lock', file_path: 'services/payment/db.py', line_start: 85, line_end: 110, ast_hash: 'l4k7'})

    CREATE (ep_pay)-[:IMPLEMENTED_BY]->(fn_root)
    CREATE (fn_root)-[:CALLS {is_async: false}]->(fn_auth)
    CREATE (fn_root)-[:CALLS {is_async: true}]->(fn_webhook)
    CREATE (fn_webhook)-[:CALLS {is_async: false}]->(fn_lock)

    // 5. Create Offending Git Commit
    CREATE (commit:Commit {
        sha: 'c3d9a107',
        author: 'alice@company.io',
        timestamp: timestamp() - 3600000,
        message: 'Refactor stripe webhook read timeout',
        diff_summary: '- timeout=3.0\n+ timeout=None'
    })
    CREATE (fn_webhook)-[:MODIFIED_BY]->(commit)

    // 6. Create Teams, Engineers & Ownership
    CREATE (team_pay:Team {id: 'team_payments', name: 'Payment Platform Team', slack_channel: '#warroom-payments'})
    CREATE (team_core:Team {id: 'team_sre', name: 'SRE Core Ops', slack_channel: '#sre-incident-response'})
    CREATE (eng_alice:Engineer {id: 'eng_alice', name: 'Alice Chen', email: 'alice@company.io', github_handle: '@alicechen', slack_handle: '@alice'})
    CREATE (eng_bob:Engineer {id: 'eng_bob', name: 'Bob Smith', email: 'bob@company.io', github_handle: '@bobsmith', slack_handle: '@bob'})

    CREATE (payment)-[:OWNED_BY]->(team_pay)
    CREATE (checkout)-[:OWNED_BY]->(team_pay)
    CREATE (commit)-[:AUTHORED_BY]->(eng_alice)
    CREATE (eng_alice)-[:MEMBER_OF]->(team_pay)
    CREATE (eng_bob)-[:MEMBER_OF]->(team_core)

    // 7. Create Validated Procedural Runbook
    CREATE (rb:Runbook {id: 'rb_net_042', title: 'Remediate Socket Read Timeout & Thread Pool Exhaustion', success_rate: 0.98})
    """

def seed_database():
    """
    Connect to FalkorDB, create HNSW vector indices, populate graph topology,
    and insert vector-indexed historical postmortems.
    """
    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", 6379))
    graph = os.getenv("PRIMARY_GRAPH", "graphsre_production")

    print(f"Connecting to FalkorDB at {host}:{port} (Graph: {graph})...")
    r = redis.Redis(host=host, port=port, decode_responses=True)

    # 1. Initialize HNSW Vector Indices
    print("Creating HNSW Vector Indices in FalkorDB...")
    try:
        r.execute_command("GRAPH.QUERY", graph, "CALL db.idx.vector.createNodeIndex('PastIncident', 'embedding', 384, 'cosine')")
        print("Created vector index on PastIncident.embedding")
    except Exception as e:
        print(f"Notice: PastIncident vector index already exists or notice: {e}")

    try:
        r.execute_command("GRAPH.QUERY", graph, "CALL db.idx.vector.createNodeIndex('Runbook', 'embedding', 384, 'cosine')")
        print("Created vector index on Runbook.embedding")
    except Exception as e:
        print(f"Notice: Runbook vector index already exists or notice: {e}")

    # 2. Seed Graph Topology
    print("Seeding Microservices, AST Call Graph, Commits & Teams...")
    r.execute_command("GRAPH.QUERY", graph, get_seed_cypher())

    # 3. Seed Past Incident Postmortem with 384-dim vecf32 Vector
    print("Seeding Episodic Memory Historical Postmortems with vecf32 embeddings...")
    embedding = generate_normalized_embedding(384)
    r.execute_command(
        "GRAPH.QUERY", graph,
        """
        CREATE (p:PastIncident {
            id: 'postmortem_inc_historical_01',
            incident_id: 'inc_historical_01',
            root_cause_summary: 'Unbounded HTTP client socket read timeout in payment webhook',
            resolution: 'Enforced 3000ms socket timeout and rolled canary deployment',
            mttr_seconds: 78,
            embedding: vecf32($vec),
            resolved_at: timestamp() - 86400000
        })
        WITH p
        MATCH (s:Service {id: 'svc_payment'})
        MATCH (rb:Runbook {id: 'rb_net_042'})
        MERGE (p)-[:AFFECTED_SERVICE]->(s)
        MERGE (p)-[:RESOLVED_BY_PLAYBOOK]->(rb)
        """,
        "--params", f'{{"vec": {embedding}}}'
    )
    print("Graph topology and vector-indexed postmortems seeded successfully.")

if __name__ == "__main__":
    seed_database()
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_seed_topology.py -v
```
Expected: PASS (all 4 tests passed).

**Step 5: Commit**

```bash
git add scripts/seed_mock_topology.py tests/test_seed_topology.py
git commit -m "feat(seed): create synthetic microservice ast topology and vector seeder"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/phase-2-falkordb-client-and-topology.md`. Two execution options:

1. **Subagent-Driven (this session)** - Dispatch fresh subagent per task, review between tasks, fast iteration.
2. **Parallel Session (separate)** - Open new session with `superpowers:executing-plans`, batch execution with checkpoints.
