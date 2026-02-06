from ultralytics import YOLO
import os

class ModelLoader:
    _models = {}

    @classmethod
    def load(cls, cam_id, model_path="best_yolo26n_29_01_2026.pt"):
        if cam_id not in cls._models:
            if not os.path.exists(model_path):
                raise RuntimeError(f"YOLO model not found: {model_path}")

            cls._models[cam_id] = YOLO(model_path)

        return cls._models[cam_id]
