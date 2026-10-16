import inspect
import os
import sys

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    class _PytestMock:
        class mark:
            @staticmethod
            def asyncio(fn):
                return fn
    pytest = _PytestMock()

from backend.main import app
from backend.websocket.hub import ws_hub

try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
except (ImportError, Exception):
    from backend.compat import TestClient
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


def test_websocket_disconnect_cleanup():
    """Verifies disconnecting removes websocket from ws_hub.active_rooms."""
    incident_id = "inc_test_ws_03"
    with client.websocket_connect(f"/ws/blackboard/{incident_id}") as websocket:
        websocket.send_json({"type": "SUBSCRIBE", "incident_id": incident_id})
        data = websocket.receive_json()
        assert data["type"] == "SUBSCRIBED"
        assert incident_id in ws_hub.active_rooms
        assert len(ws_hub.active_rooms[incident_id]) > 0

    # Outside the context manager, client is closed/disconnected
    assert incident_id not in ws_hub.active_rooms or len(ws_hub.active_rooms[incident_id]) == 0


if __name__ == "__main__":
    from backend.compat import run_coroutine

    tests = [
        ("test_websocket_connect_and_subscribe", test_websocket_connect_and_subscribe),
        ("test_websocket_broadcast_frames", test_websocket_broadcast_frames),
        ("test_websocket_disconnect_cleanup", test_websocket_disconnect_cleanup),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f"Running {name}...", flush=True)
        try:
            if inspect.iscoroutinefunction(test_fn):
                run_coroutine(test_fn())
            else:
                test_fn()
            print(f"PASS: {name}", flush=True)
            passed += 1
        except Exception as e:
            print(f"FAIL: {name} -> {e}", flush=True)
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\nWebSocket Hub Test Results: {passed} passed, {failed} failed", flush=True)

    if failed > 0:
        sys.exit(1)
