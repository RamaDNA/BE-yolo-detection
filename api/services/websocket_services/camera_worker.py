import time
import threading
import queue  # for queueing save tasks to avoid blocking the main loop
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
        self.ppe_detector = PPEDetectionService(default_cooldown=5)

        # TRACK STATE
        self.triggered_tracks = set()

        # GLOBAL LABEL DELAY FOR NOT SPAMMING IF BOXES GONE
        self.global_label_delay = {
            "no_glove": 15,   # global delay
            "no_hardhat": 5,
            "no_mask": 15
        }
        self.last_label_trigger_time = {}

        # BACKGROUND SAVING MIDDLEWARE
        self.save_queue = queue.Queue() # Antrean untuk menampung tugas simpan gambar
        self.running = False
        self.thread = None
        self.save_thread = None # Thread for saving images in the background
        self.clients = set()

    def start(self):
        if self.running:
            return
        self.running = True

        # running background save worker for saving images without blocking the main detection loop
        self.save_thread = threading.Thread(target=self._save_worker, daemon=True)
        self.save_thread.start()

        # running main detection loop
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _save_worker(self):
        """
        Middleware worker yang berjalan di background. 
        Mengambil data dari antrean dan menyimpannya ke storage.
        """
        while self.running:
            try:
                # Mengambil data dari queue (timeout 1 detik agar bisa mengecek self.running)
                task = self.save_queue.get(timeout=1.0)
                cam_id, raw_frame, annotated_frame, label = task

                # Proses penyimpanan file 
                try:
                    save_event(cam_id, annotated_frame, label)
                except Exception as e:
                    print(f"Error saving event: {e}")

                # try:
                #     save_event_for_train(cam_id, raw_frame, label)
                # except Exception as e:
                #     print(f"Error saving training screenshot: {e}")

                # response task done
                self.save_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in save worker: {e}")

    def loop(self):
        while self.running:

            # Read frame
            frame = self.stream.read()
            if frame is None:
                time.sleep(0.01) # Delay kecil jika stream kosong
                continue

            # Detection + Tracking
            boxes = self.detector.track(frame)

            # Active person IDs
            active_ids = {
                b["track_id"]
                for b in boxes
                if b.get("track_id") is not None and b["label"] in ["person", "people"]
            }

            # PPE violation detection
            events_to_trigger = self.ppe_detector.check_ppe_violations(
                boxes, self.cam_id
            )

            # Draw annotated frame
            annotated_frame = VisualizerService.draw_boxes(
                frame.copy(),
                boxes
            )

            # Save event screenshot for anti-spam
            current_time = time.time()

            for track_id, label in events_to_trigger:

                if track_id is None:
                    continue

                # block Anti-spam per track
                if track_id in self.triggered_tracks:
                    continue

                # Global delay saving example no_glove max 1 screenshot every 15 seconds
                label_delay = self.global_label_delay.get(label)

                if label_delay:
                    last_label_time = self.last_label_trigger_time.get(label, 0)

                    if current_time - last_label_time < label_delay:
                        continue  # masih delay → skip

                    # update global timer
                    self.last_label_trigger_time[label] = current_time

                # USING MIDDLEWARE (QUEUE) SAVING
                self.save_queue.put((
                    self.cam_id, 
                    frame.copy(), 
                    annotated_frame.copy(), 
                    label
                ))

                self.triggered_tracks.add(track_id)

            # Reset trigger if person left frame
            self.triggered_tracks &= active_ids

            # Line counting
            line_counts = self.line.update(boxes)
            line_counts["p1"] = self.line.p1
            line_counts["p2"] = self.line.p2

            # Count per label
            counts = self.counter.count_boxes(boxes)

            # Update shared state
            self.state.frame = annotated_frame
            self.state.frame_width = frame.shape[1]
            self.state.frame_height = frame.shape[0]
            self.state.yolo_width = 640
            self.state.yolo_height = 384
            self.state.boxes = boxes
            self.state.line = line_counts
            self.state.counts = counts
            self.state.timestamp = time.time()