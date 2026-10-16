"""
Chaos Engineering Injection Router
File: backend/api/chaos.py
"""
import time
import uuid
try:
    from fastapi import APIRouter
except ImportError:
    from backend.compat import APIRouter

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
