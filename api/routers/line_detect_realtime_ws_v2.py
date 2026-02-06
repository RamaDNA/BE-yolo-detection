# import cv2
# import base64
# import asyncio
# from fastapi import APIRouter, WebSocket
# from starlette.websockets import WebSocketDisconnect

# from services.core.model_loader import ModelLoader
# from services.core.counting_service import CountingService
# from services.core.line_detection_service import LineDetectionService

# from services.detector_service_ws import DetectorService

# router = APIRouter()

# # LOAD YOLO
# model = ModelLoader.load()
# detector = DetectorService(model)
# counter = CountingService()

# # Default line
# line_counter = LineDetectionService(
#     p1=(0, 300),
#     p2=(640, 300),
#     target_labels=["person"]
# )

# # CAMERA STREAM
# cam = "rtsp://admin:jembo123@192.168.10.203:554/Streaming/Channels/101"
# camera = cv2.VideoCapture(cam)  # GANTI dengan IP cam jika perlu


# @router.websocket("/ws/line-detect-realtime-v2")
# async def ws_line_realtime(websocket: WebSocket):

#     await websocket.accept()

#     print("🔗 WebSocket Connected")

#     # PARAMETER DINAMIS
#     selected_labels = None

#     try:
#         while True:

#             # === 1. TERIMA PARAMETER DARI CLIENT (opsional) ===
#             try:
#                 params = await asyncio.wait_for(websocket.receive_json(), timeout=0.0001)

#                 # Update min confidence
#                 if "min_confidence" in params:
#                     detector.min_confidence = float(params["min_confidence"])

#                 # Update labels
#                 if "labels" in params and params["labels"]:
#                     selected_labels = [
#                         l.strip().lower()
#                         for l in params["labels"].split(",")
#                         if l.strip()
#                     ]
#                     line_counter.target_labels = selected_labels

#                 # Update line
#                 if "p1x" in params and "p1y" in params:
#                     line_counter.p1 = (params["p1x"], params["p1y"])

#                 if "p2x" in params and "p2y" in params:
#                     line_counter.p2 = (params["p2x"], params["p2y"])

#             except asyncio.TimeoutError:
#                 pass  # Tidak ada update → lanjut

#             # === 2. BACA FRAME ===
#             ok, frame = camera.read()
#             if not ok:
#                 await asyncio.sleep(0.01)
#                 continue

#             # === 3. DETEKSI YOLO ===
#             boxes = detector.detect_frame(frame)

#             # Filter labels
#             if selected_labels:
#                 boxes = [b for b in boxes if b["label"].lower() in selected_labels]

#             # === 4. COUNT LABELS ===
#             counts = counter.count_boxes(boxes, labels=selected_labels)

#             # === 5. LINE CROSSING ===
#             line_result = line_counter.update(boxes)

#             # === 6. DRAWING BOXES ===
#             for b in boxes:
#                 x1, y1, x2, y2 = b["box"]
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

#             # Draw line
#             cv2.line(frame, line_counter.p1, line_counter.p2, (0, 0, 255), 2)

#             # === 7. ENCODE FRAME ===
#             _, buffer = cv2.imencode(".jpg", frame)
#             b64_frame = base64.b64encode(buffer).decode()

#             # === 8. SEND DATA VIA WEBSOCKET ===
#             await websocket.send_json({
#                 "frame": b64_frame,
#                 "counts": counts,
#                 "line_count": line_result,
#                 "boxes": boxes,
#                 "line": {
#                     "p1": line_counter.p1,
#                     "p2": line_counter.p2
#                 }
#             })

#             await asyncio.sleep(0.03)

#     except WebSocketDisconnect:
#         print("⚠ Client WebSocket disconnected")

#     except Exception as e:
#         print("❌ Error:", e)

#     finally:
#         print("🔒 WebSocket Closed")
