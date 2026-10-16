"""
Pydantic V2 Schemas for REST API Endpoints
File: backend/models.py
"""
from typing import List, Optional, Dict, Any
try:
    from pydantic import BaseModel, Field
except ImportError:
    from backend.compat import BaseModel, Field


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
