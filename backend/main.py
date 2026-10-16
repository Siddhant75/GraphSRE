"""
GraphSRE Backend Application Entrypoint
File: backend/main.py
"""
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    from backend.compat import FastAPI, CORSMiddleware, WebSocket, WebSocketDisconnect

from backend.config import settings
from backend.api.incidents import router as incidents_router
from backend.api.chaos import router as chaos_router
from backend.api.cicd import router as cicd_router
from backend.api.copilot import router as copilot_router
from backend.websocket.hub import ws_hub

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
    except Exception:
        ws_hub.disconnect(incident_id, websocket)

