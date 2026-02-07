from ultralytics import YOLO
import os
import torch

class ModelLoader:
    _models = {}

    @classmethod
    def load(cls, cam_id, model_path="best_yolo26n_no_shoes_07_02_2026.pt"):
        if cam_id not in cls._models:
            if not os.path.exists(model_path):
                raise RuntimeError(f"YOLO model not found: {model_path}")

            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[YOLO][cam:{cam_id}] Device: {device}")

            model = YOLO(model_path)
            model.to(device)

            cls._models[cam_id] = model

        return cls._models[cam_id]
