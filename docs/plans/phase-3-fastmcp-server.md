# Phase 3: FastMCP Tool Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the FastMCP autonomous tool server exposing 7 atomic Model Context Protocol tools to LLM agents for triage, causal traversal, vector memory recall, hypothesis posting, blackboard inspection, sandboxed remediation, and self-curating postmortems.

**Architecture:** FastMCP server connecting to FalkorDB Central Blackboard via Redis RESP connection pool. Enforces mathematical anti-hallucination invariants ($T_{\text{graph}} = 0 \implies C_{\text{SRE}} \le 0.65 < 0.75$), multi-hop AST call traversals, ephemeral sandboxing via native `GRAPH.COPY`, and self-curating $O(1)$ shortcut edges with continuous temporal decay ($\lambda = \frac{\ln 2}{30 \times 86400}$) and discrete Bayesian reinforcement ($\eta = 0.50$).

**Tech Stack:** Python 3.11+, FastMCP (`mcp.server.fastmcp`), redis-py (`redis.asyncio`), FalkorDB OpenCypher, Pydantic V2, pytest, pytest-asyncio.

---

### Task 3.1: FastMCP Server Initialization & Tool Harness (`server/mcp_server.py`)

**Files:**
- Create: `server/mcp_server.py`
- Test: `tests/test_mcp_server_init.py`

**Step 1: Write the failing test**

Create `tests/test_mcp_server_init.py`:
```python
import math
import pytest
from server.mcp_server import (
    calculate_c_sre,
    compute_sev_score,
    calculate_bayesian_reinforcement,
    calculate_continuous_decay,
    apply_code_modification_penalty,
    mcp,
    LAMBDA_DECAY
)

def test_calculate_c_sre_anti_hallucination_bound():
    """
    Mathematical Proof Verification:
    When T_graph = 0 (no structural AST or network topological path),
    even with maximum episodic similarity (1.0), metric SNR (1.0), and playbook success (1.0):
    C_SRE = 0.25*(1.0) + 0.35*(0.0) + 0.25*(1.0) + 0.15*(1.0) = 0.65.
    Since 0.65 < 0.75 verification threshold, ungrounded hypotheses can NEVER verify autonomously.
    """
    s_episodic = 1.0
    t_graph = 0.0  # Disconnected / hallucinated causal path
    e_metric = 1.0
    h_success = 1.0
    
    score = calculate_c_sre(s_episodic, t_graph, e_metric, h_success)
    assert score == 0.65
    assert score < 0.75, "Security Invariant Violated: Ungrounded hypothesis breached verification threshold"

def test_calculate_c_sre_grounded_reaches_verification():
    """Verify that a topologically grounded hypothesis (T_graph = 1.0) with strong telemetry passes 0.75."""
    score = calculate_c_sre(s_episodic=0.90, t_graph=1.0, e_metric=0.85, h_success=0.80)
    # 0.25*0.90 + 0.35*1.0 + 0.25*0.85 + 0.15*0.80 = 0.225 + 0.35 + 0.2125 + 0.12 = 0.9075
    assert pytest.approx(score, 0.001) == 0.9075
    assert score >= 0.75

def test_compute_sev_score_tier1_pagerank():
    """Verify SevScore formula: 40*Tier + 35*PageRank + 25*NormalizedInDegree."""
    # Tier 1 (1.0), PageRank 0.90, InDegree 6 (capped at 1.0)
    # 40*1.0 + 35*0.90 + 25*1.0 = 40 + 31.5 + 25 = 96.5 -> SEV_1
    score = compute_sev_score(tier="TIER_1", pagerank=0.90, in_degree=6)
    assert pytest.approx(score, 0.01) == 96.5
    assert score >= 85.0

def test_compute_sev_score_tier3_low_centrality():
    """Verify SevScore for low-tier leaf service."""
    # Tier 3 (0.3), PageRank 0.10, InDegree 1 (1/5 = 0.2)
    # 40*0.3 + 35*0.10 + 25*0.2 = 12 + 3.5 + 5.0 = 20.5 -> SEV_4 (< 35)
    score = compute_sev_score(tier="TIER_3", pagerank=0.10, in_degree=1)
    assert pytest.approx(score, 0.01) == 20.5
    assert score < 35.0

def test_calculate_bayesian_reinforcement():
    """Verify discrete Bayesian reinforcement: W_new = W + 0.50 * (1 - W)."""
    initial_w = 0.60
    new_w = calculate_bayesian_reinforcement(initial_w, eta=0.50)
    assert pytest.approx(new_w, 0.001) == 0.80

    # Reinforce again from 0.80: 0.80 + 0.5*(0.20) = 0.90
    new_w2 = calculate_bayesian_reinforcement(new_w, eta=0.50)
    assert pytest.approx(new_w2, 0.001) == 0.90

def test_calculate_continuous_decay_half_life():
    """
    Verify continuous exponential decay formula: W(t) = W_last * e^(-lambda * delta_t).
    With lambda = ln(2) / (30 * 86400), elapsed time of 30 days must halve the weight.
    """
    initial_w = 1.0
    thirty_days_seconds = 30 * 86400
    decayed_w = calculate_continuous_decay(initial_w, delta_seconds=thirty_days_seconds)
    assert pytest.approx(decayed_w, 0.001) == 0.50

def test_apply_code_modification_penalty():
    """Verify 70% Bayesian penalty upon code modification (W * 0.30)."""
    w = 0.90
    penalized_w = apply_code_modification_penalty(w)
    assert pytest.approx(penalized_w, 0.001) == 0.27

def test_fastmcp_server_instance():
    """Verify FastMCP server instance initialization and metadata."""
    assert mcp.name == "GraphSRE-Blackboard-Engine"
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_mcp_server_init.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'server.mcp_server'`

**Step 3: Write minimal implementation**

Create `server/mcp_server.py`:
```python
"""
GraphSRE FastMCP Autonomous Blackboard Server
File: server/mcp_server.py

Provides 7 atomic Model Context Protocol tools for autonomous SRE agents interacting
with the FalkorDB Central Blackboard.
"""
import os
import math
import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from server.falkordb_client import FalkorDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("graphsre.mcp")

# FastMCP Server Initialization
mcp = FastMCP(
    "GraphSRE-Blackboard-Engine",
    instructions="Autonomous SRE & Code Brain MCP Server connecting to FalkorDB Central Blackboard."
)

# Global FalkorDB Client instance
db_client = FalkorDBClient()

# Decay Constant: lambda = ln(2) / (30 * 86400 seconds) ~= 2.6734e-7 s^-1
LAMBDA_DECAY: float = math.log(2.0) / (30.0 * 86400.0)

def calculate_c_sre(
    s_episodic: float,
    t_graph: float,
    e_metric: float,
    h_success: float
) -> float:
    """
    Computes Composite Confidence Score:
    C_SRE = 0.25*S_episodic + 0.35*T_graph + 0.25*E_metric + 0.15*H_success

    Anti-Hallucination Invariant:
    If T_graph == 0.0, the theoretical maximum score with perfect episodic memory,
    metric SNR, and runbook success is 0.25(1) + 0.35(0) + 0.25(1) + 0.15(1) = 0.65.
    Since 0.65 < 0.75 verification threshold, an ungrounded theory can NEVER autonomously verify.
    """
    return (0.25 * s_episodic) + (0.35 * t_graph) + (0.25 * e_metric) + (0.15 * h_success)

def compute_sev_score(tier: str, pagerank: float, in_degree: int) -> float:
    """
    Computes Topology-Weighted Dynamic Severity Score:
    SevScore = 40*TierWeight + 35*PageRank + 25*NormalizedInDegree
    """
    tier_weight = 1.0 if tier == "TIER_1" else (0.6 if tier == "TIER_2" else 0.3)
    normalized_indegree = 1.0 if in_degree >= 5 else (in_degree / 5.0)
    return (40.0 * tier_weight) + (35.0 * pagerank) + (25.0 * normalized_indegree)

def calculate_bayesian_reinforcement(current_w: float, eta: float = 0.50) -> float:
    """
    Discrete Bayesian Reinforcement upon incident recurrence confirming shortcut:
    W_new = W + eta * (1.0 - W)
    """
    return current_w + (eta * (1.0 - current_w))

def calculate_continuous_decay(
    w_last: float,
    delta_seconds: float,
    lambda_decay: float = LAMBDA_DECAY
) -> float:
    """
    Continuous Exponential Temporal Decay:
    W(t) = W(t_last) * e^(-lambda * delta_t)
    """
    return w_last * math.exp(-lambda_decay * delta_seconds)

def apply_code_modification_penalty(w: float) -> float:
    """
    Immediate 70% Bayesian penalty triggered when Git commits modify a function
    pointed to by an incoming [:CAUSED_BY_SHORTCUT] edge (W * 0.30).
    """
    return w * 0.30

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_mcp_server_init.py -v
```
Expected: PASS (all 8 invariant and mathematical tests pass).

**Step 5: Commit**

```bash
git add server/mcp_server.py tests/test_mcp_server_init.py
git commit -m "feat(mcp): initialize fastmcp server harness and mathematical anti-hallucination invariants"
```

---

### Task 3.2: Triage & Causal Traversal Tools (`graphsre_triage_alert`, `graphsre_traverse_causal_path`)

**Files:**
- Modify: `server/mcp_server.py`
- Test: `tests/test_mcp_triage_traversal.py`

**Step 1: Write the failing test**

Create `tests/test_mcp_triage_traversal.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from server.mcp_server import (
    graphsre_triage_alert,
    graphsre_traverse_causal_path
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
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_mcp_triage_traversal.py -v
```
Expected: FAIL with `ImportError: cannot import name 'graphsre_triage_alert' from 'server.mcp_server'`

**Step 3: Write minimal implementation**

Append tools to `server/mcp_server.py`:
```python
@mcp.tool()
async def graphsre_triage_alert(
    alert_id: str,
    fingerprint: str,
    alert_name: str,
    source: str,
    target_service: str,
    metric_value: float,
    threshold: float,
    timestamp: int
) -> Dict[str, Any]:
    """
    Tool 1: Ingests raw telemetry alert, maps it to affected service, clusters via topology,
    and computes 3-hop upstream blast radius and PageRank SevScore.
    """
    query = """
    MATCH (s:Service {name: $target_service})
    MERGE (i:Incident {state: 'DETECTED'})
      ON CREATE SET i.id = 'inc_' + randomUUID(),
                    i.started_at = $timestamp,
                    i.primary_service = s.name,
                    i.composite_confidence = 0.0
    CREATE (a:Alert {
        id: $alert_id,
        fingerprint: $fingerprint,
        name: $alert_name,
        source: $source,
        metric_value: $metric_value,
        threshold: $threshold,
        timestamp: $timestamp
    })
    CREATE (i)-[:HAS_ALERT]->(a)
    CREATE (a)-[:AFFECTS]->(s)

    WITH i, s, a
    OPTIONAL MATCH path = (upstream:Service)-[:DEPENDS_ON*1..3]->(s)
    WITH i, s, a, collect(DISTINCT upstream) AS blast_services, count(DISTINCT upstream) AS upstream_count

    OPTIONAL MATCH (s)<-[dep:DEPENDS_ON]-(caller:Service)
    WITH i, s, a, blast_services, upstream_count, count(DISTINCT caller) AS in_degree
    WITH i, s, a, blast_services, upstream_count, in_degree,
         (CASE s.tier WHEN 'TIER_1' THEN 1.0 WHEN 'TIER_2' THEN 0.6 ELSE 0.3 END) AS tier_weight,
         coalesce(s.pagerank, 0.5) AS pagerank_val,
         (CASE WHEN in_degree > 5 THEN 1.0 ELSE (in_degree / 5.0) END) AS normalized_indegree

    WITH i, s, a, blast_services, upstream_count,
         ((40.0 * tier_weight) + (35.0 * pagerank_val) + (25.0 * normalized_indegree)) AS sev_score

    SET i.blast_radius_count = upstream_count,
        i.state = 'TRIAGED',
        i.severity = CASE 
            WHEN sev_score >= 85.0 OR s.tier = 'TIER_1' OR upstream_count > 5 THEN 'SEV_1'
            WHEN sev_score >= 60.0 THEN 'SEV_2'
            WHEN sev_score >= 35.0 THEN 'SEV_3'
            ELSE 'SEV_4'
        END

    RETURN i.id AS incident_id,
           i.severity AS severity,
           upstream_count AS blast_radius,
           [n IN blast_services | n.name] AS impacted_services,
           sev_score;
    """
    params = {
        "target_service": target_service,
        "timestamp": timestamp,
        "alert_id": alert_id,
        "fingerprint": fingerprint,
        "alert_name": alert_name,
        "source": source,
        "metric_value": metric_value,
        "threshold": threshold
    }
    raw = await db_client.execute_query(query, params)
    
    # Parse header and row
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        row = raw[1][0]
        return {
            "status": "TRIAGED",
            "incident_id": row[0],
            "severity": row[1],
            "blast_radius": row[2],
            "impacted_services": row[3],
            "sev_score": row[4]
        }
    return {"status": "TRIAGED", "raw": raw}

@mcp.tool()
async def graphsre_traverse_causal_path(
    incident_id: str,
    service_name: str,
    max_depth: int = 4,
    time_window_hours: int = 6
) -> Dict[str, Any]:
    """
    Tool 2: Cross-layer multi-hop traversal from service down to Tree-sitter AST functions
    and Git commits.
    """
    query = """
    MATCH (i:Incident {id: $incident_id})
    MATCH (s:Service {name: $service_name})-[:EXPOSES]->(e:Endpoint)-[:IMPLEMENTED_BY]->(root_fn:Function)
    MATCH call_path = (root_fn)-[:CALLS*0..6]->(target_fn:Function)
    MATCH (target_fn)-[:MODIFIED_BY]->(c:Commit)
    WHERE length(call_path) <= $max_depth
      AND c.timestamp >= (timestamp() - ($time_window_hours * 3600000))
    OPTIONAL MATCH (c)-[:AUTHORED_BY]->(eng:Engineer)
    OPTIONAL MATCH (s)-[:OWNED_BY]->(tm:Team)
    WITH s, e, root_fn, target_fn, c, eng, tm, length(call_path) AS call_depth
    RETURN target_fn.qualified_name AS culprit_function,
           target_fn.file_path AS file_path,
           target_fn.line_start AS line_start,
           target_fn.line_end AS line_end,
           c.sha AS culprit_commit,
           c.author AS author,
           eng.slack_handle AS author_slack,
           tm.name AS owning_team,
           c.message AS commit_message,
           c.diff_summary AS diff_summary,
           call_depth
    ORDER BY c.timestamp DESC, call_depth ASC
    LIMIT 5;
    """
    params = {
        "incident_id": incident_id,
        "service_name": service_name,
        "max_depth": max_depth,
        "time_window_hours": time_window_hours
    }
    raw = await db_client.execute_query(query, params)
    
    culprits = []
    if raw and len(raw) > 1:
        for row in raw[1]:
            culprits.append({
                "culprit_function": row[0],
                "file_path": row[1],
                "line_start": row[2],
                "line_end": row[3],
                "culprit_commit": row[4],
                "author": row[5],
                "author_slack": row[6],
                "owning_team": row[7],
                "commit_message": row[8],
                "diff_summary": row[9],
                "call_depth": row[10]
            })
            
    return {"incident_id": incident_id, "culprits": culprits}
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_mcp_triage_traversal.py -v
```
Expected: PASS (all triage and causal traversal tests pass).

**Step 5: Commit**

```bash
git add server/mcp_server.py tests/test_mcp_triage_traversal.py
git commit -m "feat(mcp): implement graphsre_triage_alert and graphsre_traverse_causal_path tools"
```

---

### Task 3.3: Memory Retrieval & Hypothesis Deliberation Tools (`graphsre_query_memory`, `graphsre_post_hypothesis`, `graphsre_get_blackboard_state`)

**Files:**
- Modify: `server/mcp_server.py`
- Test: `tests/test_mcp_memory_hypothesis.py`

**Step 1: Write the failing test**

Create `tests/test_mcp_memory_hypothesis.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from server.mcp_server import (
    graphsre_query_memory,
    graphsre_post_hypothesis,
    graphsre_get_blackboard_state
)

@pytest.mark.asyncio
async def test_graphsre_query_memory():
    """Verify hybrid retrieval executing HNSW vector query and calculating Composite Confidence C_SRE."""
    mock_results = [
        ["prior_incident_id", "past_summary", "past_resolution", "episodic_sim", "suggested_runbook_id", "playbook_title", "composite_confidence"],
        [
            [
                "postmortem_inc_prev_41",
                "Socket timeout stripped in payment gateway",
                "Reverted commit and reinstated 3s timeout",
                0.94,
                "rb_payment_timeout",
                "Payment Gateway Timeout Playbook",
                0.915
            ]
        ]
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
            top_k=3
        )
        assert len(result["matches"]) == 1
        m = result["matches"][0]
        assert m["prior_incident_id"] == "postmortem_inc_prev_41"
        assert m["episodic_sim"] == 0.94
        assert m["suggested_runbook_id"] == "rb_payment_timeout"
        assert m["composite_confidence"] == 0.915

@pytest.mark.asyncio
async def test_graphsre_post_hypothesis():
    """Verify posting a hypothesis attaches evidence nodes and transitions incident state to HYPOTHESIS_FORMED."""
    mock_post_res = [
        ["hypothesis_id", "status", "attached_count"],
        [["hyp_99b1", "PROPOSED", 2]]
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_post_res
        
        evidence = [
            {"evidence_type": "METRIC_SPIKE", "source": "Prometheus", "payload": "Latency p99 4850ms", "confidence": 0.95},
            {"evidence_type": "AST_DIFF", "source": "git diff", "payload": "- timeout=3.0\n+ timeout=None", "confidence": 0.98}
        ]
        
        res = await graphsre_post_hypothesis(
            incident_id="inc_8f3a12",
            agent_id="RCA_Agent",
            statement="Stripped timeout in payment client causes socket thread starvation",
            target_commit_sha="c3d9a107",
            initial_confidence=0.88,
            evidence_items=evidence
        )
        
        assert res["hypothesis_id"] == "hyp_99b1"
        assert res["status"] == "PROPOSED"
        assert res["attached_count"] == 2

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
                [{"hypothesis_id": "hyp_99b1", "statement": "Timeout stripped", "confidence": 0.915}]
            ]
        ]
    ]
    with patch("server.mcp_server.db_client.execute_query", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_snapshot
        
        bb = await graphsre_get_blackboard_state("inc_8f3a12")
        assert bb["incident_id"] == "inc_8f3a12"
        assert bb["lifecycle_state"] == "HYPOTHESIS_FORMED"
        assert bb["severity"] == "SEV_1"
        assert len(bb["alerts"]) == 1
        assert len(bb["hypotheses"]) == 1
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_mcp_memory_hypothesis.py -v
```
Expected: FAIL with `ImportError: cannot import name 'graphsre_query_memory' from 'server.mcp_server'`

**Step 3: Write minimal implementation**

Append tools to `server/mcp_server.py`:
```python
@mcp.tool()
async def graphsre_query_memory(
    incident_id: str,
    hypothesis_id: str,
    service_name: str,
    query_vector: List[float],
    metric_snr: float,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Tool 3: Hybrid Retrieval across HNSW Vector memory, topological structural reachability,
    and procedural runbook graphs. Computes Composite Confidence C_SRE.
    """
    query = """
    CALL db.idx.vector.queryNodes('PastIncident', 'embedding', $top_k, vecf32($query_vector))
    YIELD node AS past_incident, score AS episodic_sim
    MATCH (past_incident)-[:AFFECTED_SERVICE]->(s:Service {name: $service_name})
    OPTIONAL MATCH (past_incident)-[:RESOLVED_BY_PLAYBOOK]->(rb:Runbook)
    MATCH (h:Hypothesis {id: $hypothesis_id})-[:TARGETS]->(culprit_target)

    WITH h, past_incident, episodic_sim, rb, s, culprit_target
    OPTIONAL MATCH path = (s)-[:EXPOSES]->(:Endpoint)-[:IMPLEMENTED_BY]->(root_fn:Function)-[:CALLS*0..4]->(suspect_fn:Function)
    WHERE suspect_fn = culprit_target OR (suspect_fn)-[:MODIFIED_BY]->(culprit_target)
    WITH h, past_incident, episodic_sim, rb,
         (CASE WHEN count(path) > 0 THEN 1.0 ELSE 0.0 END) AS t_graph,
         coalesce(rb.success_rate, 0.70) AS h_success,
         $metric_snr AS e_metric

    WITH h, past_incident, episodic_sim, rb, t_graph, e_metric, h_success,
         ((0.25 * episodic_sim) + (0.35 * t_graph) + (0.25 * e_metric) + (0.15 * h_success)) AS c_sre

    SET h.composite_confidence = c_sre

    RETURN past_incident.id AS prior_incident_id,
           past_incident.root_cause_summary AS past_summary,
           past_incident.resolution AS past_resolution,
           episodic_sim,
           rb.id AS suggested_runbook_id,
           rb.title AS playbook_title,
           c_sre AS composite_confidence;
    """
    params = {
        "hypothesis_id": hypothesis_id,
        "service_name": service_name,
        "query_vector": query_vector,
        "metric_snr": metric_snr,
        "top_k": top_k
    }
    raw = await db_client.execute_query(query, params)
    
    matches = []
    if raw and len(raw) > 1:
        for row in raw[1]:
            matches.append({
                "prior_incident_id": row[0],
                "past_summary": row[1],
                "past_resolution": row[2],
                "episodic_sim": row[3],
                "suggested_runbook_id": row[4],
                "playbook_title": row[5],
                "composite_confidence": row[6]
            })
    return {"incident_id": incident_id, "hypothesis_id": hypothesis_id, "matches": matches}

@mcp.tool()
async def graphsre_post_hypothesis(
    incident_id: str,
    agent_id: str,
    statement: str,
    target_commit_sha: str,
    initial_confidence: float,
    evidence_items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Tool 4: Atomic Hypothesis creation, evidence attachment, confidence validation,
    and FSM state transition to HYPOTHESIS_FORMED.
    """
    query = """
    MATCH (i:Incident {id: $incident_id})
    MATCH (c:Commit {sha: $target_commit_sha})
    CREATE (h:Hypothesis {
        id: 'hyp_' + randomUUID(),
        agent_id: $agent_id,
        statement: $statement,
        composite_confidence: $initial_confidence,
        status: 'PROPOSED',
        created_at: timestamp()
    })
    CREATE (i)-[:HAS_HYPOTHESIS]->(h)
    CREATE (h)-[:TARGETS]->(c)

    WITH h, i
    UNWIND $evidence_items AS ev
    CREATE (e:Evidence {
        id: 'ev_' + randomUUID(),
        type: ev.evidence_type,
        source: ev.source,
        payload: ev.payload,
        confidence_score: ev.confidence,
        timestamp: timestamp()
    })
    CREATE (h)-[:SUPPORTED_BY {weight: ev.confidence}]->(e)

    WITH i, h, count(e) AS attached_count
    SET i.state = 'HYPOTHESIS_FORMED'
    RETURN h.id AS hypothesis_id, h.status AS status, attached_count;
    """
    params = {
        "incident_id": incident_id,
        "agent_id": agent_id,
        "statement": statement,
        "target_commit_sha": target_commit_sha,
        "initial_confidence": initial_confidence,
        "evidence_items": evidence_items
    }
    raw = await db_client.execute_query(query, params)
    
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        row = raw[1][0]
        return {
            "hypothesis_id": row[0],
            "status": row[1],
            "attached_count": row[2]
        }
    return {"status": "HYPOTHESIS_POSTED", "raw": raw}

@mcp.tool()
async def graphsre_get_blackboard_state(incident_id: str) -> Dict[str, Any]:
    """
    Tool 5: Reads full incident subgraph including lifecycle state, severity, active alerts,
    hypotheses, attached evidence, and consensus votes.
    """
    query = """
    MATCH (i:Incident {id: $incident_id})
    OPTIONAL MATCH (i)-[:HAS_ALERT]->(a:Alert)
    WITH i, collect(DISTINCT {
        id: a.id,
        name: a.name,
        metric_value: a.metric_value,
        threshold: a.threshold,
        timestamp: a.timestamp
    }) AS alerts

    OPTIONAL MATCH (i)-[:HAS_HYPOTHESIS]->(h:Hypothesis)
    OPTIONAL MATCH (h)-[:SUPPORTED_BY]->(e:Evidence)
    OPTIONAL MATCH (voter)-[v:VOTED_ON]->(h)
    WITH i, alerts, h,
         count(DISTINCT e) AS evidence_count,
         collect(DISTINCT {type: e.type, confidence: e.confidence_score}) AS evidence_samples,
         collect(DISTINCT {voter: coalesce(voter.name, voter.id, voter.agent_id), decision: v.decision, weight: v.weight, reason: v.reasoning}) AS votes

    WITH i, alerts, collect(DISTINCT {
        hypothesis_id: h.id,
        statement: h.statement,
        status: h.status,
        confidence: h.composite_confidence,
        evidence_count: evidence_count,
        evidence_samples: evidence_samples,
        votes: votes
    }) AS hypotheses

    RETURN i.id AS incident_id,
           i.state AS lifecycle_state,
           i.severity AS severity,
           i.blast_radius_count AS blast_radius,
           i.started_at AS started_at,
           alerts,
           hypotheses;
    """
    raw = await db_client.execute_query(query, {"incident_id": incident_id})
    
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        row = raw[1][0]
        return {
            "incident_id": row[0],
            "lifecycle_state": row[1],
            "severity": row[2],
            "blast_radius": row[3],
            "started_at": row[4],
            "alerts": row[5],
            "hypotheses": row[6]
        }
    return {"incident_id": incident_id, "blackboard": raw}
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_mcp_memory_hypothesis.py -v
```
Expected: PASS (all memory, hypothesis, and blackboard tests pass).

**Step 5: Commit**

```bash
git add server/mcp_server.py tests/test_mcp_memory_hypothesis.py
git commit -m "feat(mcp): implement graphsre_query_memory, graphsre_post_hypothesis and graphsre_get_blackboard_state tools"
```

---

### Task 3.4: Sandboxed Remediation & Self-Curating Postmortem Tools (`graphsre_execute_remediation_step`, `graphsre_commit_postmortem` with `[:CAUSED_BY_SHORTCUT]` and Bayesian decay)

**Files:**
- Modify: `server/mcp_server.py`
- Test: `tests/test_mcp_remediation_postmortem.py`

**Step 1: Write the failing test**

Create `tests/test_mcp_remediation_postmortem.py`:
```python
import pytest
from unittest.mock import patch, AsyncMock
from server.mcp_server import (
    graphsre_execute_remediation_step,
    graphsre_commit_postmortem,
    decay_stale_shortcut_edges,
    prune_obsolete_shortcut_edges
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
            dry_run=True
        )
        
        mock_sandbox.assert_called_once_with("inc_8f3a12")
        assert result["dry_run"] is True
        assert result["sandbox_id"] == "sandbox_inc_8f3a12"
        assert result["plan_id"] == "plan_canary_01"
        assert result["execution_state"] == "CANARY_ACTIVE"

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
            embedding=dummy_embedding
        )
        
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
        
        mock_exec.return_value = [["edges_deleted"], [[1]]]
        prune_res = await prune_obsolete_shortcut_edges()
        assert prune_res == 1
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_mcp_remediation_postmortem.py -v
```
Expected: FAIL with `ImportError: cannot import name 'graphsre_execute_remediation_step' from 'server.mcp_server'`

**Step 3: Write minimal implementation**

Append tools to `server/mcp_server.py`:
```python
@mcp.tool()
async def graphsre_execute_remediation_step(
    incident_id: str,
    hypothesis_id: str,
    action_type: str,
    target_entity: str,
    command_payload: str,
    rollback_payload: str,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Tool 6: Remediation plan execution & state transition inside the active incident graph.
    If dry_run=True, forks ephemeral sandbox in sub-15ms via native GRAPH.COPY.
    """
    sandbox_id = None
    target_graph = None
    
    if dry_run:
        sandbox_id = await db_client.create_sandbox(incident_id)
        target_graph = sandbox_id
        logger.info(f"Remediation dry_run active in ephemeral sandbox: {sandbox_id}")
    
    query = """
    MATCH (i:Incident {id: $incident_id})-[:HAS_HYPOTHESIS]->(h:Hypothesis {id: $hypothesis_id})
    CREATE (plan:RemediationPlan {
        id: 'plan_' + randomUUID(),
        action_type: $action_type,
        target_entity: $target_entity,
        command_payload: $command_payload,
        rollback_payload: $rollback_payload,
        execution_state: 'CANARY_ACTIVE',
        created_at: timestamp()
    })
    CREATE (h)-[:GENERATES_PLAN]->(plan)
    SET i.state = 'REMEDIATING',
        h.status = 'REMEDIATING'
    RETURN plan.id AS plan_id, plan.execution_state AS execution_state, i.state AS incident_state;
    """
    params = {
        "incident_id": incident_id,
        "hypothesis_id": hypothesis_id,
        "action_type": action_type,
        "target_entity": target_entity,
        "command_payload": command_payload,
        "rollback_payload": rollback_payload
    }
    raw = await db_client.execute_query(query, params, graph=target_graph)
    
    plan_id = "plan_unknown"
    exec_state = "CANARY_ACTIVE"
    incident_state = "REMEDIATING"
    
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        row = raw[1][0]
        plan_id = row[0]
        exec_state = row[1]
        incident_state = row[2]
        
    return {
        "dry_run": dry_run,
        "sandbox_id": sandbox_id,
        "plan_id": plan_id,
        "execution_state": exec_state,
        "incident_state": incident_state
    }

@mcp.tool()
async def graphsre_commit_postmortem(
    incident_id: str,
    root_cause_summary: str,
    resolution_summary: str,
    mttr_seconds: int,
    embedding: List[float]
) -> Dict[str, Any]:
    """
    Tool 7: Finalizes resolved incident, writes postmortem embedding into HNSW episodic memory,
    and compiles verified causal paths into self-curating O(1) shortcut edges.
    """
    query = """
    MATCH (i:Incident {id: $incident_id})
    SET i.state = 'RESOLVED',
        i.resolved_at = timestamp(),
        i.mttr_seconds = $mttr_seconds

    CREATE (p:PastIncident {
        id: 'postmortem_' + i.id,
        incident_id: i.id,
        root_cause_summary: $root_cause_summary,
        resolution: $resolution_summary,
        mttr_seconds: $mttr_seconds,
        embedding: vecf32($embedding),
        resolved_at: timestamp()
    })
    CREATE (i)-[:ARCHIVED_AS]->(p)

    WITH i, p
    MATCH (i)-[:HAS_ALERT]->(:Alert)-[:AFFECTS]->(s:Service)
    MERGE (p)-[:AFFECTED_SERVICE]->(s)

    WITH i, p
    MATCH (i)-[:HAS_ALERT]->(a:Alert)
    MATCH (i)-[:HAS_HYPOTHESIS]->(h:Hypothesis)-[:TARGETS]->(culprit)
    WHERE h.status IN ['HYPOTHESIS_VERIFIED', 'REMEDIATING', 'RESOLVED']

    MERGE (a)-[r:CAUSED_BY_SHORTCUT]->(culprit)
      ON CREATE SET r.weight = 1.0,
                    r.occurrences = 1,
                    r.last_seen = timestamp(),
                    r.stale = false
      ON MATCH SET r.weight = r.weight + (0.50 * (1.0 - r.weight)),
                   r.occurrences = r.occurrences + 1,
                   r.last_seen = timestamp(),
                   r.stale = false

    RETURN p.id AS postmortem_id, i.state AS final_lifecycle_state, r.weight AS shortcut_edge_weight;
    """
    params = {
        "incident_id": incident_id,
        "root_cause_summary": root_cause_summary,
        "resolution_summary": resolution_summary,
        "mttr_seconds": mttr_seconds,
        "embedding": embedding
    }
    raw = await db_client.execute_query(query, params)
    
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        row = raw[1][0]
        return {
            "postmortem_id": row[0],
            "final_lifecycle_state": row[1],
            "shortcut_edge_weight": row[2]
        }
    return {"status": "POSTMORTEM_COMMITTED", "raw": raw}

async def decay_stale_shortcut_edges() -> int:
    """Maintenance query applying continuous temporal decay to idle shortcut edges."""
    query = """
    MATCH ()-[r:CAUSED_BY_SHORTCUT]->()
    WHERE r.last_seen < (timestamp() - 86400000)
    WITH r, (timestamp() - r.last_seen) / 1000.0 AS elapsed_sec
    SET r.weight = r.weight * exp(-0.00000026734 * elapsed_sec)
    RETURN count(r) AS edges_updated;
    """
    raw = await db_client.execute_query(query)
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        return int(raw[1][0][0])
    return 0

async def prune_obsolete_shortcut_edges() -> int:
    """Maintenance query pruning dead shortcut edges (W < 0.15 or stale > 90 days)."""
    query = """
    MATCH ()-[r:CAUSED_BY_SHORTCUT]->()
    WHERE r.weight < 0.15 OR (r.stale = true AND r.last_seen < (timestamp() - (90 * 86400000)))
    DELETE r
    RETURN count(r) AS edges_deleted;
    """
    raw = await db_client.execute_query(query)
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        return int(raw[1][0][0])
    return 0
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_mcp_remediation_postmortem.py -v
```
Expected: PASS (all remediation, postmortem, and shortcut decay tests pass).

**Step 5: Commit**

```bash
git add server/mcp_server.py tests/test_mcp_remediation_postmortem.py
git commit -m "feat(mcp): implement remediation sandboxing, postmortem archival and shortcut decay tools"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/phase-3-fastmcp-server.md`.

**Two execution options:**
1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration.
2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints.
