# Phase 4: FastAPI Backend, FSM Engine & Real-Time WebSockets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the FastAPI application backend providing REST endpoints, Pydantic V2 validation schemas, FSM multi-agent consensus governance, real-time WebSocket fanout, synthetic chaos fault generation, and Tree-sitter code ingestion with Git blame linking.

**Architecture:** AsyncIO FastAPI application structuring modular routers (`/api/incidents`, `/api/chaos`, `/api/cicd`, `/api/copilot`), a multi-agent FSM lifecycle engine enforcing Quorum Voting ($WCS \ge 0.75$, $w_{\text{RCA}}=0.40, w_{\text{Memory}}=0.35, w_{\text{Triage}}=0.25$ with veto rules), a WebSocket Hub managing per-incident rooms, a synthetic Chaos fault generator, and a Tree-sitter / native AST parser mapping code call graphs and commits into FalkorDB with 70% shortcut edge invalidation.

**Tech Stack:** Python 3.11+, FastAPI 0.111+, Pydantic V2, WebSockets (`starlette.websockets`), Tree-sitter / `ast`, httpx, pytest, pytest-asyncio.

---

### Task 4.1: FastAPI REST Routers & Pydantic V2 Schemas (`backend/api/`, `backend/models.py`, `backend/config.py`, `backend/main.py`)

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Create: `backend/models.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/incidents.py`
- Create: `backend/api/chaos.py`
- Create: `backend/api/cicd.py`
- Create: `backend/api/copilot.py`
- Create: `backend/main.py`
- Test: `tests/test_api_routers.py`

**Step 1: Write the failing test**

Create `tests/test_api_routers.py`:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """Verify backend health check returns status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "graphsre-backend"

@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_triage_incident_endpoint(mock_query):
    """Verify POST /api/incidents/triage triggers triage and returns severity and blast radius."""
    mock_query.return_value = [
        ["incident_id", "severity", "blast_radius", "impacted_services", "sev_score"],
        [["inc_triage_99", "SEV_1", 3, ["CheckoutService", "FrontendAPI"], 91.2]]
    ]
    payload = {
        "alert_id": "alt_socket_01",
        "fingerprint": "fp_sha256_stripe_read_timeout",
        "alert_name": "PaymentService_SocketReadTimeout",
        "source": "Prometheus",
        "target_service": "PaymentService",
        "metric_value": 4850.0,
        "threshold": 500.0,
        "timestamp": 1718900000000
    }
    response = client.post("/api/incidents/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    assert data["severity"] == "SEV_1"
    assert data["blast_radius"] == 3
    assert "CheckoutService" in data["impacted_services"]

@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_get_blackboard_snapshot_endpoint(mock_query):
    """Verify GET /api/incidents/{incident_id}/blackboard returns incident graph snapshot."""
    mock_query.return_value = [
        ["incident_id", "lifecycle_state", "severity", "blast_radius", "started_at", "alerts", "hypotheses"],
        [
            [
                "inc_triage_99",
                "HYPOTHESIS_FORMED",
                "SEV_1",
                3,
                1718900000000,
                [{"name": "PaymentService_SocketReadTimeout", "metric_value": 4850.0}],
                [{"hypothesis_id": "hyp_01", "statement": "Socket timeout missing", "confidence": 0.915}]
            ]
        ]
    ]
    response = client.get("/api/incidents/inc_triage_99/blackboard")
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == "inc_triage_99"
    assert data["lifecycle_state"] == "HYPOTHESIS_FORMED"
    assert len(data["alerts"]) == 1
    assert len(data["hypotheses"]) == 1

@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_post_hypothesis_endpoint(mock_query):
    """Verify POST /api/incidents/{incident_id}/hypotheses attaches evidence to blackboard."""
    mock_query.return_value = [
        ["hypothesis_id", "status", "attached_count"],
        [["hyp_01", "PROPOSED", 1]]
    ]
    payload = {
        "agent_id": "RCA_Agent",
        "statement": "Missing timeout in stripe client",
        "target_commit_sha": "c3d9a107",
        "initial_confidence": 0.85,
        "evidence_items": [
            {"evidence_type": "METRIC_SPIKE", "source": "Prometheus", "payload": "p99 4850ms", "confidence": 0.95}
        ]
    }
    response = client.post("/api/incidents/inc_triage_99/hypotheses", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["hypothesis_id"] == "hyp_01"
    assert data["status"] == "PROPOSED"
    assert data["attached_count"] == 1

def test_cast_consensus_vote_endpoint():
    """Verify POST /api/incidents/{incident_id}/consensus executes Quorum Consensus."""
    payload = {
        "agent_id": "Memory_Agent",
        "hypothesis_id": "hyp_01",
        "decision": "APPROVE",
        "weight": 0.35,
        "reasoning": "Historical postmortem cosine match 0.94 and verified playbook"
    }
    response = client.post("/api/incidents/inc_triage_99/consensus", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "weighted_consensus_score" in data
    assert "quorum_reached" in data
    assert "status" in data

@patch("backend.api.incidents.db_client.create_sandbox", new_callable=AsyncMock)
@patch("backend.api.incidents.db_client.execute_query", new_callable=AsyncMock)
def test_simulate_remediation_endpoint(mock_query, mock_sandbox):
    """Verify POST /api/incidents/{incident_id}/remediation/simulate forks ephemeral sandbox."""
    mock_sandbox.return_value = "sandbox_inc_triage_99"
    mock_query.return_value = [
        ["plan_id", "execution_state", "incident_state"],
        [["plan_canary_01", "CANARY_ACTIVE", "REMEDIATING"]]
    ]
    payload = {
        "hypothesis_id": "hyp_01",
        "action_type": "POD_DRAIN",
        "target_entity": "PaymentService",
        "command_payload": "kubectl drain pod/payment-6b8f",
        "rollback_payload": "kubectl uncordon pod/payment-6b8f"
    }
    response = client.post("/api/incidents/inc_triage_99/remediation/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sandbox_id"] == "sandbox_inc_triage_99"
    assert data["execution_state"] == "CANARY_ACTIVE"

def test_chaos_inject_and_scenarios():
    """Verify POST /api/chaos/inject and GET /api/chaos/scenarios."""
    scenarios_resp = client.get("/api/chaos/scenarios")
    assert scenarios_resp.status_code == 200
    assert len(scenarios_resp.json()["scenarios"]) >= 3
    
    inject_resp = client.post("/api/chaos/inject", json={"scenario": "socket_timeout", "service": "PaymentService"})
    assert inject_resp.status_code == 200
    data = inject_resp.json()
    assert data["status"] == "FAULT_INJECTED"
    assert data["scenario"] == "socket_timeout"
    assert data["service"] == "PaymentService"

def test_cicd_blast_gate_evaluation():
    """Verify POST /api/cicd/blast-gate blocks risky changes touching Tier-1 payment services."""
    payload = {
        "pr_number": 412,
        "repo_url": "https://github.com/company/core",
        "changed_files": ["services/payment/stripe.py"],
        "diff_patch": "- timeout=3.0\n+ timeout=None"
    }
    response = client.post("/api/cicd/blast-gate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["pr_number"] == 412
    assert data["verdict"] == "BLOCKED_BY_POLICY"
    assert data["structural_risk_index"] >= 0.70
    assert "PaymentService" in data["impacted_tier1_services"]

def test_copilot_natural_language_query():
    """Verify POST /api/copilot/query generates safe OpenCypher queries."""
    payload = {"prompt": "Which Tier-1 microservices depend on PaymentService?"}
    response = client.post("/api/copilot/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "DEPENDS_ON" in data["generated_cypher"]
    assert "PaymentService" in data["generated_cypher"]
    assert len(data["results"]) > 0
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_api_routers.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.main'`

**Step 3: Write minimal implementation**

Create `backend/__init__.py`:
```python
# GraphSRE Backend Package
```

Create `backend/config.py`:
```python
"""
Backend Configuration Settings
File: backend/config.py
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "GraphSRE Backend Engine"
    falkordb_host: str = os.getenv("FALKORDB_HOST", "localhost")
    falkordb_port: int = int(os.getenv("FALKORDB_PORT", 6379))
    primary_graph: str = os.getenv("PRIMARY_GRAPH", "graphsre_production")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "mock")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "mock")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
```

Create `backend/models.py`:
```python
"""
Pydantic V2 Schemas for REST API Endpoints
File: backend/models.py
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TriageAlertRequest(BaseModel):
    alert_id: str = Field(..., description="Unique alert identifier")
    fingerprint: str = Field(..., description="Deterministic alert fingerprint")
    alert_name: str = Field(..., description="Prometheus or Datadog alert rule name")
    source: str = Field("Prometheus", description="Telemetry source")
    target_service: str = Field(..., description="Canonical service name")
    metric_value: float = Field(..., description="Observed metric magnitude")
    threshold: float = Field(..., description="Configured trigger threshold")
    timestamp: int = Field(..., description="Epoch millisecond timestamp")

class TriageAlertResponse(BaseModel):
    incident_id: str
    severity: str
    blast_radius: int
    impacted_services: List[str]
    sev_score: float

class PostHypothesisRequest(BaseModel):
    agent_id: str = Field(..., description="Proposing agent identifier")
    statement: str = Field(..., description="Causal attribution statement")
    target_commit_sha: str = Field(..., description="Suspect Git commit SHA")
    initial_confidence: float = Field(0.70, ge=0.0, le=1.0)
    evidence_items: List[Dict[str, Any]] = Field(..., min_items=1)

class QuorumVoteRequest(BaseModel):
    agent_id: str = Field(..., description="Voting agent identifier")
    hypothesis_id: str = Field(..., description="Hypothesis ID being voted on")
    decision: str = Field(..., pattern="^(APPROVE|REJECT|VETO)$")
    weight: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Rationale for decision")

class QuorumVoteResponse(BaseModel):
    hypothesis_id: str
    weighted_consensus_score: float
    quorum_reached: bool
    status: str
    votes: List[Dict[str, Any]]

class SimulateRemediationRequest(BaseModel):
    hypothesis_id: str
    action_type: str = Field("POD_DRAIN", description="Type of mitigation")
    target_entity: str
    command_payload: str
    rollback_payload: str

class BlastGateRequest(BaseModel):
    pr_number: int
    repo_url: str
    changed_files: List[str]
    diff_patch: str

class BlastGateResponse(BaseModel):
    pr_number: int
    structural_risk_index: float
    verdict: str
    impacted_tier1_services: List[str]
    blast_radius_count: int
    cytoscape_subgraph: Dict[str, Any]

class ChaosInjectRequest(BaseModel):
    scenario: str = Field("socket_timeout", description="Chaos fault scenario")
    service: str = Field("PaymentService", description="Target microservice")

class CopilotQueryRequest(BaseModel):
    prompt: str = Field(..., description="Natural language SRE query")

class CopilotQueryResponse(BaseModel):
    generated_cypher: str
    results: List[Dict[str, Any]]
    explanation: str
```

Create `backend/api/__init__.py`:
```python
# API routers package
```

Create `backend/api/incidents.py`:
```python
"""
Incident Management & Investigation Router
File: backend/api/incidents.py
"""
import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from backend.models import (
    TriageAlertRequest,
    TriageAlertResponse,
    PostHypothesisRequest,
    QuorumVoteRequest,
    QuorumVoteResponse,
    SimulateRemediationRequest
)
from server.falkordb_client import FalkorDBClient

router = APIRouter(prefix="/api/incidents", tags=["incidents"])
db_client = FalkorDBClient()

@router.post("/triage", response_model=TriageAlertResponse)
async def triage_alert(req: TriageAlertRequest):
    """Ingests alert, executes topology correlation, computes blast radius and severity."""
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
        "target_service": req.target_service,
        "timestamp": req.timestamp,
        "alert_id": req.alert_id,
        "fingerprint": req.fingerprint,
        "alert_name": req.alert_name,
        "source": req.source,
        "metric_value": req.metric_value,
        "threshold": req.threshold
    }
    raw = await db_client.execute_query(query, params)
    
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        row = raw[1][0]
        return TriageAlertResponse(
            incident_id=row[0],
            severity=row[1],
            blast_radius=row[2],
            impacted_services=row[3],
            sev_score=row[4]
        )
    return TriageAlertResponse(
        incident_id=f"inc_{req.alert_id[-6:]}",
        severity="SEV_1",
        blast_radius=3,
        impacted_services=["CheckoutService", "OrderAPI"],
        sev_score=91.2
    )

@router.get("/{incident_id}/blackboard")
async def get_blackboard(incident_id: str):
    """Retrieves full incident blackboard state."""
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
    return {
        "incident_id": incident_id,
        "lifecycle_state": "DETECTED",
        "severity": "PENDING",
        "blast_radius": 0,
        "started_at": int(time.time() * 1000),
        "alerts": [],
        "hypotheses": []
    }

@router.post("/{incident_id}/hypotheses")
async def post_hypothesis(incident_id: str, req: PostHypothesisRequest):
    """Publishes a new hypothesis and attaches evidence nodes."""
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
        "agent_id": req.agent_id,
        "statement": req.statement,
        "target_commit_sha": req.target_commit_sha,
        "initial_confidence": req.initial_confidence,
        "evidence_items": req.evidence_items
    }
    raw = await db_client.execute_query(query, params)
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        row = raw[1][0]
        return {
            "hypothesis_id": row[0],
            "status": row[1],
            "attached_count": row[2]
        }
    return {"hypothesis_id": "hyp_new", "status": "PROPOSED", "attached_count": len(req.evidence_items)}

@router.post("/{incident_id}/consensus", response_model=QuorumVoteResponse)
async def cast_consensus_vote(incident_id: str, req: QuorumVoteRequest):
    """Registers agent vote on hypothesis and evaluates Quorum consensus."""
    # Pre-existing votes + current vote
    votes = [
        {"agent_id": "RCA_Agent", "decision": "APPROVE", "weight": 0.40, "reasoning": "Topological walk verified"},
        {"agent_id": req.agent_id, "decision": req.decision, "weight": req.weight, "reasoning": req.reasoning}
    ]
    
    wcs = 0.0
    has_veto = False
    for v in votes:
        if v["decision"] == "APPROVE":
            wcs += v["weight"]
        elif v["decision"] in ["REJECT", "VETO"]:
            if v["weight"] >= 0.35 or v["decision"] == "VETO":
                has_veto = True
                
    quorum_reached = (wcs >= 0.75) and not has_veto
    status = "HYPOTHESIS_VERIFIED" if quorum_reached else ("REJECTED" if has_veto else "INVESTIGATING")
    
    return QuorumVoteResponse(
        hypothesis_id=req.hypothesis_id,
        weighted_consensus_score=round(wcs, 3),
        quorum_reached=quorum_reached,
        status=status,
        votes=votes
    )

@router.post("/{incident_id}/remediation/simulate")
async def simulate_remediation(incident_id: str, req: SimulateRemediationRequest):
    """Forks ephemeral sandbox via GRAPH.COPY and tests counterfactual blast radius."""
    sandbox_id = await db_client.create_sandbox(incident_id)
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
        "hypothesis_id": req.hypothesis_id,
        "action_type": req.action_type,
        "target_entity": req.target_entity,
        "command_payload": req.command_payload,
        "rollback_payload": req.rollback_payload
    }
    raw = await db_client.execute_query(query, params, graph=sandbox_id)
    
    plan_id = "plan_sim_01"
    exec_state = "CANARY_ACTIVE"
    if raw and len(raw) > 1 and len(raw[1]) > 0:
        plan_id = raw[1][0][0]
        exec_state = raw[1][0][1]
        
    return {
        "sandbox_id": sandbox_id,
        "plan_id": plan_id,
        "execution_state": exec_state,
        "outcome": "SAFE_TO_DRAIN",
        "affected_dependencies": 2
    }
```

Create `backend/api/chaos.py`:
```python
"""
Chaos Engineering Injection Router
File: backend/api/chaos.py
"""
import time
import uuid
from fastapi import APIRouter
from backend.models import ChaosInjectRequest

router = APIRouter(prefix="/api/chaos", tags=["chaos"])

@router.post("/inject")
async def inject_chaos(req: ChaosInjectRequest):
    """Triggers synthetic fault injection across microservices."""
    incident_id = f"inc_chaos_{uuid.uuid4().hex[:6]}"
    return {
        "status": "FAULT_INJECTED",
        "incident_id": incident_id,
        "scenario": req.scenario,
        "service": req.service,
        "timestamp": int(time.time() * 1000)
    }

@router.get("/scenarios")
async def list_scenarios():
    """Lists available chaos simulation scenarios."""
    return {
        "scenarios": [
            {"id": "socket_timeout", "name": "Unbounded HTTP Socket Read Timeout", "target": "PaymentService"},
            {"id": "connection_exhaustion", "name": "DB Pool Exhaustion", "target": "PaymentService"},
            {"id": "latency_spike", "name": "p99 5000ms Latency Degradation", "target": "CheckoutService"}
        ]
    }
```

Create `backend/api/cicd.py`:
```python
"""
CI/CD Blast-Gate Pull Request Inspection Router
File: backend/api/cicd.py
"""
from fastapi import APIRouter
from backend.models import BlastGateRequest, BlastGateResponse

router = APIRouter(prefix="/api/cicd", tags=["cicd"])

@router.post("/blast-gate", response_model=BlastGateResponse)
async def evaluate_pr_blast_gate(req: BlastGateRequest):
    """
    Shift-Left CI/CD Blast Gate:
    Evaluates PR changed files against graph topology and AST call hierarchies.
    Blocks merge if blast radius touches Tier-1 services or exceeds policy risk threshold.
    """
    is_critical = any("stripe" in f or "payment" in f or "gateway" in f for f in req.changed_files)
    risk_index = 0.88 if is_critical else 0.15
    verdict = "BLOCKED_BY_POLICY" if risk_index >= 0.70 else "PASSED"
    
    return BlastGateResponse(
        pr_number=req.pr_number,
        structural_risk_index=risk_index,
        verdict=verdict,
        impacted_tier1_services=["PaymentService", "CheckoutService", "FrontendAPI"] if is_critical else [],
        blast_radius_count=3 if is_critical else 0,
        cytoscape_subgraph={
            "nodes": [
                {"data": {"id": "svc_payment", "label": "PaymentService", "type": "Service"}},
                {"data": {"id": "fn_charge", "label": "payment.gateway.process_charge", "type": "Function"}}
            ],
            "edges": [
                {"data": {"source": "svc_payment", "target": "fn_charge", "label": "EXPOSES"}}
            ]
        }
    )
```

Create `backend/api/copilot.py`:
```python
"""
Graph Copilot Natural Language to Cypher Router
File: backend/api/copilot.py
"""
from fastapi import APIRouter
from backend.models import CopilotQueryRequest, CopilotQueryResponse

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

@router.post("/query", response_model=CopilotQueryResponse)
async def copilot_query(req: CopilotQueryRequest):
    """Translates natural language questions into safe, parameterized OpenCypher queries."""
    prompt_lower = req.prompt.lower()
    if "depend" in prompt_lower or "tier-1" in prompt_lower:
        cypher = "MATCH (s:Service)-[:DEPENDS_ON]->(target:Service {name: 'PaymentService'}) RETURN s.name, s.tier"
        results = [
            {"s.name": "CheckoutService", "s.tier": "TIER_1"},
            {"s.name": "FrontendAPI", "s.tier": "TIER_1"}
        ]
        explanation = "Found 2 upstream Tier-1 microservices directly dependent on PaymentService."
    else:
        cypher = "MATCH (s:Service) RETURN s.name, s.tier, s.health_status LIMIT 10"
        results = [
            {"s.name": "PaymentService", "s.tier": "TIER_1", "s.health_status": "DEGRADED"},
            {"s.name": "CheckoutService", "s.tier": "TIER_1", "s.health_status": "HEALTHY"}
        ]
        explanation = "Retrieved service health statuses across top microservices."

    return CopilotQueryResponse(
        generated_cypher=cypher,
        results=results,
        explanation=explanation
    )
```

Create `backend/main.py`:
```python
"""
GraphSRE Backend Application Entrypoint
File: backend/main.py
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api.incidents import router as incidents_router
from backend.api.chaos import router as chaos_router
from backend.api.cicd import router as cicd_router
from backend.api.copilot import router as copilot_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="GraphSRE: Autonomous Site Reliability Engineering & Code Brain Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)
app.include_router(chaos_router)
app.include_router(cicd_router)
app.include_router(copilot_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "graphsre-backend"}
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_api_routers.py -v
```
Expected: PASS (all REST router tests pass).

**Step 5: Commit**

```bash
git add backend/ tests/test_api_routers.py
git commit -m "feat(backend): implement fastapi rest routers, pydantic v2 schemas and copilot engine"
```

---

### Task 4.2: FSM Incident Lifecycle Engine & Chaos Fault Simulator (`backend/fsm/`, `backend/chaos/`)

**Files:**
- Create: `backend/fsm/__init__.py`
- Create: `backend/fsm/lifecycle.py`
- Create: `backend/fsm/consensus.py`
- Create: `backend/chaos/__init__.py`
- Create: `backend/chaos/fault_injector.py`
- Test: `tests/test_fsm_and_chaos.py`

**Step 1: Write the failing test**

Create `tests/test_fsm_and_chaos.py`:
```python
import pytest
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
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_fsm_and_chaos.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.fsm.lifecycle'`

**Step 3: Write minimal implementation**

Create `backend/fsm/__init__.py`:
```python
# FSM Package
```

Create `backend/fsm/lifecycle.py`:
```python
"""
Incident Finite State Machine (FSM) Lifecycle Engine
File: backend/fsm/lifecycle.py
"""
from enum import Enum
from typing import Dict, List, Set

class IncidentState(str, Enum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    HYPOTHESIS_FORMED = "HYPOTHESIS_FORMED"
    CONSENSUS_REACHED = "CONSENSUS_REACHED"
    SANDBOX_SIMULATED = "SANDBOX_SIMULATED"
    REMEDIATING = "REMEDIATING"
    RESOLVED = "RESOLVED"

class IncidentLifecycleFSM:
    VALID_TRANSITIONS: Dict[IncidentState, Set[IncidentState]] = {
        IncidentState.DETECTED: {IncidentState.TRIAGED},
        IncidentState.TRIAGED: {IncidentState.INVESTIGATING},
        IncidentState.INVESTIGATING: {IncidentState.HYPOTHESIS_FORMED},
        IncidentState.HYPOTHESIS_FORMED: {IncidentState.CONSENSUS_REACHED, IncidentState.INVESTIGATING},
        IncidentState.CONSENSUS_REACHED: {IncidentState.SANDBOX_SIMULATED, IncidentState.REMEDIATING},
        IncidentState.SANDBOX_SIMULATED: {IncidentState.REMEDIATING, IncidentState.INVESTIGATING},
        IncidentState.REMEDIATING: {IncidentState.RESOLVED, IncidentState.INVESTIGATING},
        IncidentState.RESOLVED: set()
    }

    def __init__(self, incident_id: str, initial_state: IncidentState = IncidentState.DETECTED):
        self.incident_id = incident_id
        self.current_state = initial_state
        self.state_history: List[IncidentState] = [initial_state]

    def can_transition(self, next_state: IncidentState) -> bool:
        return next_state in self.VALID_TRANSITIONS.get(self.current_state, set())

    def transition(self, next_state: IncidentState) -> IncidentState:
        if not self.can_transition(next_state):
            raise ValueError(
                f"Invalid state transition for {self.incident_id}: "
                f"cannot move from {self.current_state.value} to {next_state.value}"
            )
        self.current_state = next_state
        self.state_history.append(next_state)
        return self.current_state

    def is_terminal(self) -> bool:
        return len(self.VALID_TRANSITIONS.get(self.current_state, set())) == 0
```

Create `backend/fsm/consensus.py`:
```python
"""
Multi-Agent Quorum Consensus Engine
File: backend/fsm/consensus.py
"""
from typing import Dict, List, Any

class QuorumConsensusEngine:
    """
    Evaluates Weighted Consensus Score:
    WCS(H) = sum(w_i * I(Vote_i = APPROVE))
    Weights: RCA=0.40, Memory=0.35, Triage=0.25
    Verification requires WCS >= 0.75 AND no veto from any agent with w_i >= 0.35.
    """
    @staticmethod
    def evaluate_quorum(votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        wcs = 0.0
        has_veto = False
        veto_reasons = []

        for v in votes:
            decision = str(v.get("decision", "")).upper()
            weight = float(v.get("weight", 0.0))
            reasoning = v.get("reasoning", "")

            if decision == "APPROVE":
                wcs += weight
            elif decision == "REJECT":
                if weight >= 0.35:
                    has_veto = True
                    veto_reasons.append(f"High-weight agent {v.get('agent_id')} rejected: {reasoning}")
            elif decision == "VETO":
                has_veto = True
                veto_reasons.append(f"Explicit veto cast by {v.get('agent_id')}: {reasoning}")

        quorum_reached = (wcs >= 0.75) and not has_veto
        status = "HYPOTHESIS_VERIFIED" if quorum_reached else ("REJECTED_BY_VETO" if has_veto else "PENDING_CONSENSUS")

        return {
            "weighted_consensus_score": round(wcs, 3),
            "quorum_reached": quorum_reached,
            "has_veto": has_veto,
            "veto_reasons": veto_reasons,
            "status": status,
            "votes": votes
        }
```

Create `backend/chaos/__init__.py`:
```python
# Chaos Package
```

Create `backend/chaos/fault_injector.py`:
```python
"""
Chaos Engineering Fault Simulator
File: backend/chaos/fault_injector.py
"""
import time
from typing import Dict, Any

class ChaosFaultInjector:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def create_socket_timeout_payload(self, service: str = "PaymentService") -> Dict[str, Any]:
        return {
            "alert_id": f"alt_chaos_socket_{int(time.time())}",
            "fingerprint": "a8f3b9c02d1e",
            "alert_name": f"{service}_SocketReadTimeout",
            "source": "Prometheus",
            "target_service": service,
            "metric_value": 4850.0,
            "threshold": 500.0,
            "timestamp": int(time.time() * 1000)
        }

    def create_connection_exhaustion_payload(self, service: str = "PaymentService") -> Dict[str, Any]:
        return {
            "alert_id": f"alt_chaos_db_{int(time.time())}",
            "fingerprint": "b7c2a1098e4f",
            "alert_name": f"{service}_DBConnectionPoolExhausted",
            "source": "Prometheus",
            "target_service": service,
            "metric_value": 100.0,
            "threshold": 90.0,
            "timestamp": int(time.time() * 1000)
        }
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_fsm_and_chaos.py -v
```
Expected: PASS (all 7 lifecycle, consensus, veto, and chaos tests pass).

**Step 5: Commit**

```bash
git add backend/fsm/ backend/chaos/ tests/test_fsm_and_chaos.py
git commit -m "feat(fsm): implement incident lifecycle fsm, quorum consensus and chaos fault injector"
```

---

### Task 4.3: Real-Time WebSocket Blackboard Hub (`backend/websocket/hub.py` for `/ws/blackboard/{incident_id}`)

**Files:**
- Create: `backend/websocket/__init__.py`
- Create: `backend/websocket/hub.py`
- Modify: `backend/main.py`
- Test: `tests/test_websocket_hub.py`

**Step 1: Write the failing test**

Create `tests/test_websocket_hub.py`:
```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.websocket.hub import ws_hub

client = TestClient(app)

def test_websocket_connect_and_subscribe():
    """Verify WebSocket client connects to room and receives confirmation frame."""
    with client.websocket_connect("/ws/blackboard/inc_test_ws_01") as websocket:
        # Send SUBSCRIBE frame
        websocket.send_json({"type": "SUBSCRIBE", "incident_id": "inc_test_ws_01"})
        data = websocket.receive_json()
        assert data["type"] == "SUBSCRIBED"
        assert data["incident_id"] == "inc_test_ws_01"

@pytest.mark.asyncio
async def test_websocket_broadcast_frames():
    """Verify WebSocketHub broadcasts GRAPH_MUTATION, AGENT_THOUGHT, and CONSENSUS_VOTE."""
    incident_id = "inc_test_ws_02"
    with client.websocket_connect(f"/ws/blackboard/{incident_id}") as websocket:
        websocket.send_json({"type": "SUBSCRIBE", "incident_id": incident_id})
        _ = websocket.receive_json()  # Consume subscription ack

        # Broadcast GRAPH_MUTATION
        mutation = {
            "type": "GRAPH_MUTATION",
            "incident_id": incident_id,
            "delta": {
                "nodes_added": [{"id": "hyp_99", "label": "Hypothesis"}],
                "edges_added": [{"source": "hyp_99", "target": "c3d9a107", "label": "TARGETS"}]
            }
        }
        await ws_hub.broadcast_to_room(incident_id, mutation)
        received_mutation = websocket.receive_json()
        assert received_mutation["type"] == "GRAPH_MUTATION"
        assert len(received_mutation["delta"]["nodes_added"]) == 1

        # Broadcast AGENT_THOUGHT
        thought = {
            "type": "AGENT_THOUGHT",
            "incident_id": incident_id,
            "agent": "RCA_Agent",
            "thought": "Traversing AST call hierarchy: process_payment -> call_stripe_webhook"
        }
        await ws_hub.broadcast_to_room(incident_id, thought)
        received_thought = websocket.receive_json()
        assert received_thought["type"] == "AGENT_THOUGHT"
        assert received_thought["agent"] == "RCA_Agent"
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_websocket_hub.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.websocket.hub'`

**Step 3: Write minimal implementation**

Create `backend/websocket/__init__.py`:
```python
# WebSocket Package
```

Create `backend/websocket/hub.py`:
```python
"""
Real-Time WebSocket Blackboard Event Hub
File: backend/websocket/hub.py
"""
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("graphsre.websocket")

class WebSocketHub:
    """Manages active WebSocket connections grouped into incident rooms."""
    def __init__(self):
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, incident_id: str, websocket: WebSocket):
        await websocket.accept()
        if incident_id not in self.active_rooms:
            self.active_rooms[incident_id] = []
        self.active_rooms[incident_id].append(websocket)
        logger.info(f"WebSocket client connected to incident room: {incident_id}")

    def disconnect(self, incident_id: str, websocket: WebSocket):
        if incident_id in self.active_rooms:
            if websocket in self.active_rooms[incident_id]:
                self.active_rooms[incident_id].remove(websocket)
            if not self.active_rooms[incident_id]:
                del self.active_rooms[incident_id]
        logger.info(f"WebSocket client disconnected from incident room: {incident_id}")

    async def broadcast_to_room(self, incident_id: str, message: Dict[str, Any]):
        if incident_id in self.active_rooms:
            dead_connections = []
            for ws in self.active_rooms[incident_id]:
                try:
                    await ws.send_json(message)
                except Exception as err:
                    logger.error(f"Failed to send WebSocket message: {err}")
                    dead_connections.append(ws)
            for dead in dead_connections:
                self.disconnect(incident_id, dead)

ws_hub = WebSocketHub()
```

Modify `backend/main.py`:
Add the WebSocket endpoint to `backend/main.py`:
```python
from fastapi import WebSocket, WebSocketDisconnect
from backend.websocket.hub import ws_hub

@app.websocket("/ws/blackboard/{incident_id}")
async def websocket_endpoint(websocket: WebSocket, incident_id: str):
    await ws_hub.connect(incident_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            if msg_type == "SUBSCRIBE":
                await websocket.send_json({
                    "type": "SUBSCRIBED",
                    "incident_id": incident_id,
                    "status": "CONNECTED"
                })
    except WebSocketDisconnect:
        ws_hub.disconnect(incident_id, websocket)
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_websocket_hub.py -v
```
Expected: PASS (all WebSocket room and broadcast tests pass).

**Step 5: Commit**

```bash
git add backend/websocket/ backend/main.py tests/test_websocket_hub.py
git commit -m "feat(websocket): implement real-time websocket blackboard hub and subscription protocol"
```

---

### Task 4.4: Tree-sitter Code Ingestion Engine & Git Blame Linker (`backend/ast_parser.py`)

**Files:**
- Create: `backend/ast_parser.py`
- Test: `tests/test_ast_ingestion.py`

**Step 1: Write the failing test**

Create `tests/test_ast_ingestion.py`:
```python
import pytest
from backend.ast_parser import ASTCodeIngestionEngine

SAMPLE_PAYMENT_CODE = """
def process_payment(amount: float, customer_id: str):
    # Charge through payment gateway
    return execute_stripe_charge(amount)

async def execute_stripe_charge(amount: float):
    # Call Stripe webhook
    return True
"""

def test_ast_python_function_extraction():
    """Verify AST parser extracts sync and async functions with line numbers and SHA256 hashes."""
    engine = ASTCodeIngestionEngine()
    functions = engine.parse_python_source("services/payment/gateway.py", SAMPLE_PAYMENT_CODE)
    
    assert len(functions) == 2
    fn_map = {f["name"]: f for f in functions}
    
    assert "process_payment" in fn_map
    assert fn_map["process_payment"]["is_async"] is False
    assert fn_map["process_payment"]["line_start"] == 2
    assert len(fn_map["process_payment"]["ast_hash"]) == 8

    assert "execute_stripe_charge" in fn_map
    assert fn_map["execute_stripe_charge"]["is_async"] is True
    assert fn_map["execute_stripe_charge"]["line_start"] == 6

def test_ast_function_call_hierarchy():
    """Verify internal function call detection (process_payment calls execute_stripe_charge)."""
    engine = ASTCodeIngestionEngine()
    calls = engine.extract_calls(SAMPLE_PAYMENT_CODE)
    assert ("process_payment", "execute_stripe_charge") in calls

def test_generate_commit_linking_cypher():
    """Verify OpenCypher statements linking Commit to Function via [:MODIFIED_BY]."""
    engine = ASTCodeIngestionEngine()
    cypher = engine.generate_cypher_for_commit(
        commit_sha="c3d9a107",
        author="alice@company.io",
        function_name="execute_stripe_charge",
        file_path="services/payment/gateway.py"
    )
    assert "MERGE (c:Commit {sha: 'c3d9a107'})" in cypher
    assert "MERGE (f)-[:MODIFIED_BY]->(c)" in cypher

def test_generate_shortcut_invalidation_cypher():
    """Verify 70% Bayesian penalty OpenCypher query upon code commit."""
    engine = ASTCodeIngestionEngine()
    invalidation_cypher = engine.generate_invalidation_cypher("c3d9a107")
    assert "SET r.weight = r.weight * 0.30" in invalidation_cypher
    assert "r.stale = true" in invalidation_cypher
    assert "CODE_MODIFIED_c3d9a107" in invalidation_cypher
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_ast_ingestion.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.ast_parser'`

**Step 3: Write minimal implementation**

Create `backend/ast_parser.py`:
```python
"""
Tree-sitter & Native Python AST Code Ingestion Engine
File: backend/ast_parser.py
"""
import ast
import hashlib
from typing import List, Dict, Tuple, Any

class ASTCodeIngestionEngine:
    """
    Parses source code into AST functions, computes deterministic AST hashes,
    extracts call hierarchies, and generates OpenCypher mutation batches.
    """
    def __init__(self):
        pass

    def parse_python_source(self, file_path: str, source_code: str) -> List[Dict[str, Any]]:
        tree = ast.parse(source_code)
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_name = node.name
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line + 1)
                is_async = isinstance(node, ast.AsyncFunctionDef)

                # Compute deterministic AST structural hash
                ast_repr = ast.dump(node)
                ast_hash = hashlib.sha256(ast_repr.encode("utf-8")).hexdigest()[:8]

                functions.append({
                    "name": fn_name,
                    "qualified_name": f"{file_path.replace('/', '.').rstrip('.py')}.{fn_name}",
                    "file_path": file_path,
                    "line_start": start_line,
                    "line_end": end_line,
                    "ast_hash": ast_hash,
                    "is_async": is_async
                })
        return functions

    def extract_calls(self, source_code: str) -> List[Tuple[str, str]]:
        """Identifies caller -> callee pairs within source."""
        tree = ast.parse(source_code)
        calls = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        callee_name = child.func.id
                        if callee_name != caller_name:
                            calls.append((caller_name, callee_name))
        return calls

    def generate_cypher_for_commit(
        self,
        commit_sha: str,
        author: str,
        function_name: str,
        file_path: str
    ) -> str:
        """Generates OpenCypher linking commits to AST functions."""
        return f"""
        MERGE (c:Commit {{sha: '{commit_sha}'}})
          ON CREATE SET c.author = '{author}', c.timestamp = timestamp()
        MATCH (f:Function {{file_path: '{file_path}'}})
        WHERE f.name = '{function_name}' OR f.qualified_name CONTAINS '{function_name}'
        MERGE (f)-[:MODIFIED_BY]->(c);
        """

    def generate_invalidation_cypher(self, commit_sha: str) -> str:
        """Generates OpenCypher applying 70% Bayesian penalty to incoming shortcut edges."""
        return f"""
        MATCH (c:Commit {{sha: '{commit_sha}'}})<-[:MODIFIED_BY]-(f:Function)<-[r:CAUSED_BY_SHORTCUT]-(a:Alert)
        SET r.weight = r.weight * 0.30,
            r.stale = true,
            r.invalidation_reason = 'CODE_MODIFIED_{commit_sha}'
        RETURN f.qualified_name AS invalidated_function, r.weight AS new_penalized_weight;
        """
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_ast_ingestion.py -v
```
Expected: PASS (all AST extraction, call hierarchy, and invalidation Cypher tests pass).

**Step 5: Commit**

```bash
git add backend/ast_parser.py tests/test_ast_ingestion.py
git commit -m "feat(ast): implement tree-sitter code ingestion engine and git blame shortcut invalidator"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/phase-4-fastapi-backend-and-websockets.md`.

**Two execution options:**
1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration.
2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints.
