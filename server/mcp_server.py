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

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    class FastMCP:
        """Lightweight fallback for FastMCP when mcp package is not installed."""
        def __init__(self, name: str, instructions: Optional[str] = None, **kwargs: Any):
            self.name = name
            self.instructions = instructions or ""
            self._tools: Dict[str, Any] = {}

        def tool(self, *args: Any, **kwargs: Any):
            def decorator(fn: Any) -> Any:
                self._tools[fn.__name__] = fn
                return fn
            if len(args) == 1 and callable(args[0]):
                return decorator(args[0])
            return decorator

        def run(self, transport: str = "stdio") -> None:
            logger.info("FastMCP server '%s' running on transport '%s' (fallback mode)", self.name, transport)

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
    tier_upper = tier.upper() if isinstance(tier, str) else ""
    tier_weight = 1.0 if tier_upper == "TIER_1" else (0.6 if tier_upper == "TIER_2" else 0.3)
    normalized_indegree = max(0.0, min(1.0, float(in_degree) / 5.0))
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
         (CASE toUpper(coalesce(s.tier, '')) WHEN 'TIER_1' THEN 1.0 WHEN 'TIER_2' THEN 0.6 ELSE 0.3 END) AS tier_weight,
         coalesce(s.pagerank, 0.5) AS pagerank_val,
         (CASE WHEN in_degree > 5 THEN 1.0 ELSE (in_degree / 5.0) END) AS normalized_indegree

    WITH i, s, a, blast_services, upstream_count,
         ((40.0 * tier_weight) + (35.0 * pagerank_val) + (25.0 * normalized_indegree)) AS sev_score

    SET i.blast_radius_count = upstream_count,
        i.state = 'TRIAGED',
        i.severity = CASE 
            WHEN sev_score >= 85.0 OR toUpper(coalesce(s.tier, '')) = 'TIER_1' OR upstream_count > 5 THEN 'SEV_1'
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
    return {
        "status": "ERROR",
        "error": f"Target service '{target_service}' not found in active topology graph.",
        "raw": raw
    }


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
    effective_depth = max(1, min(int(max_depth), 6))
    effective_window = max(1, int(time_window_hours))

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
        "max_depth": effective_depth,
        "time_window_hours": effective_window
    }
    raw = await db_client.execute_query(query, params)

    culprits = []
    if raw and len(raw) > 1 and raw[1]:
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
    effective_top_k = max(1, min(int(top_k), 20))
    params = {
        "incident_id": incident_id,
        "hypothesis_id": hypothesis_id,
        "service_name": service_name,
        "query_vector": query_vector,
        "metric_snr": metric_snr,
        "top_k": effective_top_k
    }
    raw = await db_client.execute_query(query, params)

    matches = []
    if raw and len(raw) > 1 and raw[1]:
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
    return {
        "status": "ERROR",
        "error": f"Failed to post hypothesis: Incident '{incident_id}' or Commit '{target_commit_sha}' not found.",
        "raw": raw
    }


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
        alerts = [
            a for a in row[5]
            if isinstance(a, dict) and any(v is not None for v in a.values())
        ]
        hypotheses = [
            h for h in row[6]
            if isinstance(h, dict) and any(v is not None for v in h.values())
        ]
        return {
            "incident_id": row[0],
            "lifecycle_state": row[1],
            "severity": row[2],
            "blast_radius": row[3],
            "started_at": row[4],
            "alerts": alerts,
            "hypotheses": hypotheses
        }
    return {
        "status": "ERROR",
        "error": f"Incident '{incident_id}' not found on blackboard.",
        "incident_id": incident_id,
        "raw": raw
    }


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
    return {
        "status": "ERROR",
        "error": f"Failed to commit postmortem: Incident '{incident_id}' not found.",
        "incident_id": incident_id,
        "raw": raw
    }


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


if __name__ == "__main__":
    mcp.run(transport="stdio")


