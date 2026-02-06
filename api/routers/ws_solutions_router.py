from fastapi import APIRouter, WebSocket
from services.solutions_lib_services.solutions_manager import solutions_realtime_manager
import json
import asyncio
import cv2
import base64

router = APIRouter()

@router.websocket("/ws/solutions/{cam_id}")
async def ws_solutions(websocket: WebSocket, cam_id: str):
    await websocket.accept()

    worker = solutions_realtime_manager.registry.get(cam_id)
    if not worker:
        await websocket.send_text("CAMERA NOT REGISTERED")
        return

    worker.start()
    worker.clients.add(websocket)

    try:
        while True:
            await asyncio.sleep(0.03)
            state = worker.state

            # encode frame
            frame_base64 = None
            if state.frame is not None:
                small_frame = cv2.resize(state.frame, (640, 384))
                _, buffer = cv2.imencode(".jpg", small_frame)
                frame_base64 = base64.b64encode(buffer).decode("utf-8")

            # SOLUTIONS OUTPUT
            data = {
                "frame": frame_base64,
                
                # object count dari ObjectCounter
                "counts": getattr(state, "counts", {}),

                # region count dari RegionCounter
                "region": getattr(state, "region", {}),

                "timestamp": state.timestamp,
            }

            await websocket.send_json(data)

    except Exception:
        pass
    finally:
        worker.clients.remove(websocket)
