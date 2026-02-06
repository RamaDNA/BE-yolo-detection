import time
import threading
# import cv2

from services.core.detector_service import DetectorService
from services.core.line_detection_service import LineDetectionService
from services.core.model_loader import ModelLoader
from services.core.counting_service import CountingService
from services.core.ppe_detection_service import PPEDetectionService
from services.core.visualizer_service import VisualizerService

from services.websocket_services.stream_service import StreamService
from services.websocket_services.camera_state import CameraState
from utils.screenshot import save_event
from utils.screenshot_for_train import save_event_for_train


class CameraWorker:
    def __init__(self, cam_id, rtsp, p1, p2, labels=["person"]):
        self.cam_id = cam_id
        self.rtsp = rtsp

        self.state = CameraState()
        self.stream = StreamService(rtsp)

        self.detector = DetectorService(ModelLoader.load(self.cam_id))
        self.line = LineDetectionService(p1, p2, labels)
        self.counter = CountingService()
        self.ppe_detector = PPEDetectionService(cooldown_seconds=5)

        # 🔑 TRACK STATE
        self.last_active_ids = set()
        self.triggered_tracks = set()

        self.running = False
        self.thread = None
        self.clients = set()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def loop(self):
        while self.running:

            # 1️⃣ Read frame
            frame = self.stream.read()
            if frame is None:
                time.sleep(0.1)
                continue

            # 2️⃣ Detection + Tracking
            boxes = self.detector.track(frame)

            # 3️⃣ Active person IDs
            active_ids = {
                b["track_id"]
                for b in boxes
                if b.get("track_id") is not None and b["label"] in ["person", "people"]
            }

            # 4️⃣ PPE violation detection
            events_to_trigger = self.ppe_detector.check_ppe_violations(boxes, self.cam_id)
            violator_ids = {track_id for track_id, _ in events_to_trigger}

            # 5️⃣ Draw annotated frame (ALL boxes)
            annotated_frame = VisualizerService.draw_boxes(
                frame.copy(),
                boxes,
                violator_ids=violator_ids
            )

            # 6️⃣ Save event screenshot (ANTI-SPAM)
            for track_id, label in events_to_trigger:
                if track_id is None:
                    continue

                if track_id in self.triggered_tracks:
                    continue  # 🚫 anti-spam
                
                try:
                    save_event(self.cam_id, annotated_frame, label)
                except Exception as e:
                    print(f"Error saving event: {e}")
                try:
                    save_event_for_train(self.cam_id, frame.copy(), label)
                except Exception as e:
                    print(f"Error saving training screenshot: {e}")
                self.triggered_tracks.add(track_id)

            # 7️⃣ Reset trigger if person left frame
            self.triggered_tracks &= active_ids

            # 8️⃣ Line counting
            line_counts = self.line.update(boxes)
            # 🟡 inject line geometry
            line_counts["p1"] = self.line.p1
            line_counts["p2"] = self.line.p2
            # 9️⃣ Count per label
            counts = self.counter.count_boxes(boxes)

            # 🔟 Update shared state
            self.state.frame = annotated_frame
            self.state.frame_width = frame.shape[1]
            self.state.frame_height = frame.shape[0]
            self.state.yolo_width = 640
            self.state.yolo_height = 384
            self.state.boxes = boxes
            self.state.line = line_counts
            self.state.counts = counts
            self.state.timestamp = time.time()

            self.last_active_ids = active_ids
