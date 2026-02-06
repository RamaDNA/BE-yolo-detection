from fastapi import APIRouter, WebSocket
from services.websocket_services.realtime_manager import realtime_manager
import json
import asyncio
import cv2
import base64

router = APIRouter()

@router.websocket("/ws/realtime/{cam_id}")
async def ws_realtime(websocket: WebSocket, cam_id: str):
    await websocket.accept()

    worker = realtime_manager.registry.get(cam_id)
    if not worker:
        await websocket.send_text("CAMERA NOT REGISTERED")
        return

    worker.start()
    worker.clients.add(websocket)

    try:
        while True:
            await asyncio.sleep(0.05)
            state = worker.state

            # encode frame to base64
            frame_base64 = None
            if state.frame is not None:
                # resize frame
                small_frame = cv2.resize(state.frame, (640, 384))
                _, buffer = cv2.imencode(".jpg", small_frame)
                frame_base64 = base64.b64encode(buffer).decode("utf-8")

            data = {
                "frame":frame_base64,
                "boxes": state.boxes,
                
                "line": state.line,
                "counts": state.counts,
                "timestamp": state.timestamp,
                "frame_width": state.frame_width,
                "frame_height": state.frame_height,
                "yolo_width": state.yolo_width,
                "yolo_height": state.yolo_height,
            }
            await websocket.send_json(data)

    except Exception:
        pass
    finally:
        worker.clients.remove(websocket)
