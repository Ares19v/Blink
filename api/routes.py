"""
routes.py
FastAPI API routers for Blink video streaming, monitoring, calibration,
settings, history, and WebSocket telemetry.
"""

import asyncio
import json
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.camera_service import camera_service
from core.config_manager import load_config, save_config
from core.database import (
    get_sessions_records,
    delete_session,
    clear_sessions,
    get_database_summary,
)
from core.logger_setup import logger

router = APIRouter(prefix="/api")
ws_router = APIRouter()


# ----------------------------------------------------------------------
# Request / Response Schemas
# ----------------------------------------------------------------------

class StartMonitoringRequest(BaseModel):
    camera_index: Optional[int] = 0


class SettingsPayload(BaseModel):
    camera_index: int = Field(default=0)
    blink_rate_threshold: float = Field(default=12.0)
    notification_cooldown: int = Field(default=90)
    ear_threshold: float = Field(default=0.21)
    twenty_twenty_twenty_enabled: bool = Field(default=True)
    twenty_twenty_twenty_interval_sec: int = Field(default=1200)
    sound_enabled: bool = Field(default=True)
    calibrated: bool = Field(default=False)


# ----------------------------------------------------------------------
# Monitoring & Video Streaming
# ----------------------------------------------------------------------

def _frame_generator():
    """Yields JPEG multipart frames for MJPEG streaming."""
    while True:
        frame_bytes = camera_service.get_latest_jpeg()
        if frame_bytes is not None and camera_service.is_running():
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
            time.sleep(0.033)  # ~30 FPS
        else:
            time.sleep(0.1)


@router.get("/video_feed")
async def video_feed():
    """MJPEG streaming endpoint for HTML <img> or <canvas> tag."""
    return StreamingResponse(
        _frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/monitoring/start")
async def start_monitoring(req: StartMonitoringRequest = StartMonitoringRequest()):
    success = camera_service.start_monitoring(camera_index=req.camera_index)
    return {"status": "success", "running": success, "camera_index": req.camera_index}


@router.post("/monitoring/stop")
async def stop_monitoring():
    summary = camera_service.stop_monitoring()
    return {"status": "success", "running": False, "summary": summary}


@router.get("/monitoring/status")
async def monitoring_status():
    return {
        "running": camera_service.is_running(),
        "stats": camera_service.get_stats(),
    }


# ----------------------------------------------------------------------
# Calibration
# ----------------------------------------------------------------------

@router.post("/calibration/start")
async def start_calibration():
    if not camera_service.is_running():
        camera_service.start_monitoring()
    camera_service.start_calibration()
    return {"status": "success", "message": "Calibration started"}


@router.post("/calibration/stop")
async def stop_calibration():
    new_threshold = camera_service.stop_calibration()
    return {"status": "success", "ear_threshold": new_threshold}


@router.get("/calibration/status")
async def calibration_status():
    return camera_service.get_calibration_status()


# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------

@router.get("/settings")
async def get_settings():
    return load_config()


@router.post("/settings")
async def update_settings(settings: SettingsPayload):
    data = settings.model_dump()
    save_config(data)
    camera_service.reload_config()
    logger.info("Configuration updated via API.")
    return {"status": "success", "settings": data}


# ----------------------------------------------------------------------
# History & Analytics
# ----------------------------------------------------------------------

@router.get("/history")
async def get_history(limit: int = 50):
    return get_sessions_records(limit=limit)


@router.delete("/history/{session_id}")
async def delete_history_session(session_id: int):
    deleted = delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "deleted_id": session_id}


@router.delete("/history")
async def clear_all_history():
    clear_sessions()
    return {"status": "success", "message": "All history cleared"}


@router.get("/history/summary")
async def get_history_summary():
    return get_database_summary()


# ----------------------------------------------------------------------
# WebSocket Telemetry Handler
# ----------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


async def _handle_websocket(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            stats = camera_service.get_stats()
            stats["is_running"] = camera_service.is_running()
            await websocket.send_text(json.dumps(stats))
            await asyncio.sleep(0.005)  # Up to 60 FPS stream

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client disconnected: {e}")
        ws_manager.disconnect(websocket)



@router.websocket("/ws/telemetry")
async def websocket_telemetry_prefixed(websocket: WebSocket):
    await _handle_websocket(websocket)


@ws_router.websocket("/ws/telemetry")
async def websocket_telemetry_direct(websocket: WebSocket):
    await _handle_websocket(websocket)
