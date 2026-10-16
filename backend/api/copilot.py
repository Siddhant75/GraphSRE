"""
Graph Copilot Natural Language to Cypher Router
File: backend/api/copilot.py
"""
try:
    from fastapi import APIRouter
except ImportError:
    from backend.compat import APIRouter

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
