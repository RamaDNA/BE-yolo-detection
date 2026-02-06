from fastapi import APIRouter
from services.websocket_services.realtime_manager import realtime_manager

router = APIRouter()

@router.get("/camera/{cam_id}/state")
def get_camera_state(cam_id: str):
    state = realtime_manager.get_state(cam_id)
    if not state:
        return {"error": "not found"}

    return {
        "boxes": state.boxes,
        "line": state.line,
        "counts": state.counts,
        "timestamp": state.timestamp
    }
