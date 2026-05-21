from services.websocket_services.camera_worker import CameraWorker


class RealtimeManager:
    def __init__(self):
        self.registry = {}

    def register_camera(self, cam_id, rtsp, p1, p2, labels=["person"]):
        if cam_id not in self.registry:
            self.registry[cam_id] = CameraWorker(cam_id, rtsp, p1, p2, labels)
        return self.registry[cam_id]

    def start_all(self):
        print("Starting all cameras...")
        for worker in self.registry.values():
            worker.start()

    def stop_all(self):
        print("Stopping all cameras...")
        for worker in self.registry.values():
            worker.stop()

    def get_state(self, cam_id):
        worker = self.registry.get(cam_id)
        if worker:
            return worker.state
        return None


# GLOBAL instance
realtime_manager = RealtimeManager()