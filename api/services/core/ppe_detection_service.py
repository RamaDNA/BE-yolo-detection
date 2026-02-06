"""
PPE Detection Service
Checks for PPE violations using violation labels and track IDs
"""
import time
from collections import defaultdict

class PPEDetectionService:
    def __init__(self, cooldown_seconds=60):
        self.cooldown_seconds = cooldown_seconds
        self.last_violation_time = defaultdict(lambda: defaultdict(float))

    def check_ppe_violations(self, boxes, cam_id):
        events_to_trigger = []
        current_time = time.time()

        # ✅ ADD HERE (MATCH YOLO CLASS)
        violation_labels = [
            # # --- YOLO CLASSES ---
            "no_hardhat",
            "no_mask",
            "no_safety_vest",
            "no_glove",
            "short_sleeve",
            "no_shoes"

            # # --- OPTIONAL using Alias ---
            # "no-hardhat",
            # "no-mask",
            # "no-safety-vest",
            # "no-glove",
            # "no hardhat",
            # "no mask",
            # "no safety vest",
            # "no glove",
        ]

        for box in boxes:
            label = box["label"].lower()
            if label in violation_labels:
                track_id = box.get("track_id")
                if track_id is not None:
                    last_time = self.last_violation_time[track_id][label]
                    if current_time - last_time >= self.cooldown_seconds:
                        events_to_trigger.append((track_id, label))
                        self.last_violation_time[track_id][label] = current_time

        return events_to_trigger
