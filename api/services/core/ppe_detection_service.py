"""
PPE Detection Service
Checks for PPE violations using violation labels and track IDs
"""
import time
from collections import defaultdict

class PPEDetectionService:
    def __init__(self, default_cooldown=60):
        self.default_cooldown = default_cooldown
        
        # ✅ Custom cooldown per label
        self.label_cooldowns = {
            "no_glove": 60,          # 1 menit khusus glove
            "no_hardhat": 5,      # contoh kalau mau beda
            "no_mask": 10
        }

        self.last_violation_time = defaultdict(lambda: defaultdict(float))

    def check_ppe_violations(self, boxes, cam_id):
        events_to_trigger = []
        current_time = time.time()

        violation_labels = [
            "no_hardhat",
            "no_mask",
            "no_safety_vest",
            "no_glove",
            "short_sleeve"
        ]

        for box in boxes:
            label = box["label"].lower()

            if label in violation_labels:
                track_id = box.get("track_id")

                if track_id is not None:
                    
                    # ✅ Ambil cooldown berdasarkan label
                    cooldown = self.label_cooldowns.get(label, self.default_cooldown)

                    last_time = self.last_violation_time[track_id][label]

                    if current_time - last_time >= cooldown:
                        events_to_trigger.append((track_id, label))
                        self.last_violation_time[track_id][label] = current_time

        return events_to_trigger