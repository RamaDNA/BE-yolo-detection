import cv2
import time

class VisualizerService:
    """
    Responsible ONLY for drawing bounding boxes and overlays
    """

    @staticmethod
    def draw_boxes(frame, boxes, violator_ids=None):
        if violator_ids is None:
            violator_ids = set()

        for b in boxes:
            x1, y1, x2, y2 = map(int, [b["x1"], b["y1"], b["x2"], b["y2"]])
            label = b["label"]
            conf = b.get("confidence", 0.0)
            track_id = b.get("track_id")

            # 🎨 WARNA
            color = (0, 255, 0)  # 🟢 normal
            if track_id in violator_ids:
                color = (0, 0, 255)  # 🔴 violation

            text = f"{label} {conf:.2f}"
            if track_id is not None:
                text += f" ID:{track_id}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                text,
                (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        return frame
