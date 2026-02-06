import time
import threading
import cv2

from services.core.model_loader import ModelLoader
from services.websocket_services.stream_service import StreamService
from services.websocket_services.camera_state import CameraState

from services.solutions_lib_services.solutions_line_service import SolutionsLineService
from services.solutions_lib_services.solutions_region_service import SolutionsRegionService


class SolutionsCameraWorker:
    def __init__(self, cam_id, rtsp, region_points):
        self.cam_id = cam_id
        self.rtsp = rtsp
        self.state = CameraState()
        self.stream = StreamService(rtsp)

        # load YOLO from ModelLoader
        model = ModelLoader.load()

        # pakai LINE COUNTER (ObjectCounter)
        self.line_service = SolutionsLineService(region_points, model)

        # opsional region counter
        self.region_service = SolutionsRegionService(region_points, model)

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

            frame = self.stream.read()
            if frame is None:
                time.sleep(0.1)
                continue

            # LINE COUNTING
            line_result = self.line_service.update(frame)

            # REGION COUNTING
            region_result = self.region_service.update(frame)

            # update state
            self.state.frame = line_result.plot_im
            self.state.counts = line_result.counts
            self.state.region = region_result.counts
            self.state.timestamp = time.time()
