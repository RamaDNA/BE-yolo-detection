import cv2
import base64
import asyncio
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from services.model_loader import ModelLoader
from services.detector_service_ws import DetectorService
from services.counting_service import CountingService
from services.line_detection_service import LineDetectionService

router = APIRouter()

# LOAD YOLO MODEL
model = ModelLoader.load()
detector = DetectorService(model)
counter = CountingService()

# Default line
line_counter = LineDetectionService(
    p1=(0, 300),
    p2=(640, 300),
    target_labels=["person"]
)
cam = "rtsp://admin:jembo123@192.168.10.203:554/Streaming/Channels/101"
camera = cv2.VideoCapture(cam)  # GANTI DENGAN STREAM KAMU


@router.websocket("/ws/line-detect-realtime")
async def ws_line_realtime(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                await asyncio.sleep(0.01)
                continue

            # DETECT
            boxes = detector.detect_frame(frame)

            # Count persons
            total_count = counter.count_boxes(boxes)

            # Line crossing
            line_result = line_counter.update(boxes)

            # Draw boxes
            for b in boxes:
                x1, y1, x2, y2 = b["box"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw line
            cv2.line(frame, line_counter.p1, line_counter.p2, (0, 0, 255), 2)

            # Encode → base64
            _, buffer = cv2.imencode(".jpg", frame)
            b64_frame = base64.b64encode(buffer).decode()

            # SEND FRAME
            await websocket.send_json({
                "frame": b64_frame,
                "total_count": total_count,
                "line_count": line_result,
                "boxes": boxes
            })

            await asyncio.sleep(0.03)

    except WebSocketDisconnect:
        print("⚠ Client disconnected from WebSocket")
    except Exception as e:
        print("❌ Error in WebSocket:", e)
    finally:
        print("🔒 WebSocket connection closed")
