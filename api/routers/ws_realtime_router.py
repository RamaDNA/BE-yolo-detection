from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.websocket_services.realtime_manager import realtime_manager
import asyncio
import cv2
import base64
import time

router = APIRouter()

TARGET_FPS = 25
FRAME_TIME = 1 / TARGET_FPS  # 0.04 detik


@router.websocket("/ws/realtime/{cam_id}")
async def ws_realtime(websocket: WebSocket, cam_id: str):
    await websocket.accept()

    worker = realtime_manager.registry.get(cam_id)
    if not worker:
        await websocket.send_text("CAMERA NOT REGISTERED")
        await websocket.close()
        return

    worker.start()
    worker.clients.add(websocket)

    try:
        while True:
            loop_start = time.perf_counter()

            state = worker.state
            frame_base64 = None

            if state and state.frame is not None:
                # resize biar ringan
                small_frame = cv2.resize(state.frame, (640, 384))

                # encode jpg (quality bisa diturunin kalau mau lebih ringan)
                _, buffer = cv2.imencode(
                    ".jpg",
                    small_frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                )

                frame_base64 = base64.b64encode(buffer).decode("utf-8")

            data = {
                "frame": frame_base64,
                "boxes": state.boxes if state else [],
                "line": state.line if state else None,
                "counts": state.counts if state else {},
                "timestamp": state.timestamp if state else None,
                "frame_width": state.frame_width if state else None,
                "frame_height": state.frame_height if state else None,
                "yolo_width": state.yolo_width if state else None,
                "yolo_height": state.yolo_height if state else None,
            }

            await websocket.send_json(data)

            # =========================
            # FPS Stabilizer (25 FPS)
            # =========================
            elapsed = time.perf_counter() - loop_start
            sleep_time = FRAME_TIME - elapsed

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        print(f"Client disconnected from camera {cam_id}")

    except Exception as e:
        print("WebSocket error:", e)

    finally:
        worker.clients.discard(websocket)