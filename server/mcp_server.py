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


if __name__ == "__main__":
    mcp.run(transport="stdio")
