"""
Real-Time WebSocket Blackboard Event Hub
File: backend/websocket/hub.py
"""
import logging
from typing import Dict, List, Any

try:
    from fastapi import WebSocket
except ImportError:
    from backend.compat import WebSocket

logger = logging.getLogger("graphsre.websocket")


class WebSocketHub:
    """Manages active WebSocket connections grouped into incident rooms."""
    def __init__(self):
        self.active_rooms: Dict[str, List[Any]] = {}

    async def connect(self, incident_id: str, websocket: Any):
        await websocket.accept()
        if incident_id not in self.active_rooms:
            self.active_rooms[incident_id] = []
        self.active_rooms[incident_id].append(websocket)
        logger.info(f"WebSocket client connected to incident room: {incident_id}")

    def disconnect(self, incident_id: str, websocket: Any):
        if incident_id in self.active_rooms:
            if websocket in self.active_rooms[incident_id]:
                self.active_rooms[incident_id].remove(websocket)
            if not self.active_rooms[incident_id]:
                del self.active_rooms[incident_id]
        logger.info(f"WebSocket client disconnected from incident room: {incident_id}")

    async def broadcast_to_room(self, incident_id: str, message: Dict[str, Any]):
        if incident_id in self.active_rooms:
            dead_connections = []
            for ws in list(self.active_rooms[incident_id]):
                try:
                    await ws.send_json(message)
                except Exception as err:
                    logger.error(f"Failed to send WebSocket message: {err}")
                    dead_connections.append(ws)
            for dead in dead_connections:
                self.disconnect(incident_id, dead)


ws_hub = WebSocketHub()
