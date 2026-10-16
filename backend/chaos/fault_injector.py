"""
Chaos Engineering Fault Simulator
File: backend/chaos/fault_injector.py
"""
import time
from typing import Dict, Any


class ChaosFaultInjector:
    """
    Simulates real-world microservice infrastructure failures by generating
    deterministic Prometheus-style alert telemetry payloads and injecting them
    into the GraphSRE blackboard ingestion pipeline.
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def create_socket_timeout_payload(self, service: str = "PaymentService") -> Dict[str, Any]:
        """Creates an unbounded HTTP socket read timeout fault alert."""
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
        """Creates a database connection pool exhaustion fault alert."""
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

    def create_latency_spike_payload(self, service: str = "CheckoutService") -> Dict[str, Any]:
        """Creates a p99 latency degradation fault alert."""
        return {
            "alert_id": f"alt_chaos_lat_{int(time.time())}",
            "fingerprint": "c1f4e892d3b5",
            "alert_name": f"{service}_HighLatencyP99",
            "source": "Prometheus",
            "target_service": service,
            "metric_value": 5200.0,
            "threshold": 2000.0,
            "timestamp": int(time.time() * 1000)
        }
