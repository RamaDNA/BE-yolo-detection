from services.solutions_lib_services.solutions_camera_worker import SolutionsCameraWorker

class SolutionsRealtimeManager:
    def __init__(self):
        self.registry = {}

    def register_camera(self, cam_id, rtsp, region_points):
        if cam_id not in self.registry:
            self.registry[cam_id] = SolutionsCameraWorker(
                cam_id=cam_id,
                rtsp=rtsp,
                region_points=region_points
            )
        return self.registry[cam_id]

    def start_all(self):
        for worker in self.registry.values():
            worker.start()

    def get_state(self, cam_id):
        w = self.registry.get(cam_id)
        return w.state if w else None


solutions_realtime_manager = SolutionsRealtimeManager()
