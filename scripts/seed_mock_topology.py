"""
Realistic Microservice Graph, AST Topology & Vector Memory Seeder
File: scripts/seed_mock_topology.py
"""
import json
import logging
import math
import os
import random
import sys
from typing import List, Optional

# Optional numpy support with standard library fallback
try:
    import numpy as np
except ImportError:
    np = None

# Optional redis support with graceful fallback
try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger("graphsre.seed")


def generate_normalized_embedding(dim: int = 384) -> List[float]:
    """
    Generate an L2-normalized random unit vector of dimension `dim` (compatible with MiniLM 384-dim).
    Uses numpy if available, otherwise falls back to standard library random.gauss.
    """
    if np is not None:
        vec = np.random.randn(dim).astype(np.float32)
        norm = float(np.linalg.norm(vec))
        if norm == 0:
            return vec.tolist()
        return (vec / norm).tolist()
    else:
        raw = [random.gauss(0.0, 1.0) for _ in range(dim)]
        norm = math.sqrt(sum(x * x for x in raw))
        if norm == 0:
            return [0.0] * dim
        return [float(x / norm) for x in raw]


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
        diff_summary: '- timeout=3.0\\n+ timeout=None'
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


def seed_database(
    host: Optional[str] = None,
    port: Optional[int] = None,
    graph: Optional[str] = None,
) -> bool:
    """
    Connect to FalkorDB, create HNSW vector indices, populate graph topology,
    and insert vector-indexed historical postmortems.
    Handles exceptions gracefully if FalkorDB is not running or redis is unavailable.
    """
    if redis is None:
        print("Warning: redis package is not installed. Skipping FalkorDB connection.")
        return False

    falkor_host = host or os.getenv("FALKORDB_HOST", "localhost")
    falkor_port = int(port or os.getenv("FALKORDB_PORT", 6379))
    falkor_graph = graph or os.getenv("PRIMARY_GRAPH", "graphsre_production")

    print(f"Connecting to FalkorDB at {falkor_host}:{falkor_port} (Graph: {falkor_graph})...")
    try:
        r = redis.Redis(host=falkor_host, port=falkor_port, decode_responses=True)
        r.ping()
    except Exception as e:
        print(f"Warning: Could not connect to FalkorDB at {falkor_host}:{falkor_port}: {e}")
        return False

    # 1. Initialize HNSW Vector Indices
    print("Creating HNSW Vector Indices in FalkorDB...")
    try:
        r.execute_command(
            "GRAPH.QUERY",
            falkor_graph,
            "CALL db.idx.vector.createNodeIndex('PastIncident', 'embedding', 384, 'cosine')",
        )
        print("Created vector index on PastIncident.embedding")
    except Exception as e:
        print(f"Notice: PastIncident vector index already exists or notice: {e}")

    try:
        r.execute_command(
            "GRAPH.QUERY",
            falkor_graph,
            "CALL db.idx.vector.createNodeIndex('Runbook', 'embedding', 384, 'cosine')",
        )
        print("Created vector index on Runbook.embedding")
    except Exception as e:
        print(f"Notice: Runbook vector index already exists or notice: {e}")

    # 2. Seed Graph Topology
    print("Seeding Microservices, AST Call Graph, Commits & Teams...")
    try:
        r.execute_command("GRAPH.QUERY", falkor_graph, get_seed_cypher())
    except Exception as e:
        print(f"Error seeding graph topology: {e}")
        return False

    # 3. Seed Past Incident Postmortem with 384-dim vecf32 Vector
    print("Seeding Episodic Memory Historical Postmortems with vecf32 embeddings...")
    embedding = generate_normalized_embedding(384)
    past_incident_cypher = """
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
    """
    try:
        r.execute_command(
            "GRAPH.QUERY",
            falkor_graph,
            past_incident_cypher,
            "--params",
            json.dumps({"vec": embedding}),
        )
        print("Graph topology and vector-indexed postmortems seeded successfully.")
        return True
    except Exception as e:
        print(f"Error seeding postmortem: {e}")
        return False


if __name__ == "__main__":
    seed_database()
