import cv2

class VisualizerService:
    """
    Responsible ONLY for drawing bounding boxes and overlays
    """

    # 🔴 Semua label ini akan merah
    VIOLATION_LABELS = {
        "no_hardhat",
        "no_mask",
        "no_safety_vest",
        "no_glove",
        "short_sleeve"
    }

    @staticmethod
    def draw_boxes(frame, boxes, violator_ids=None):
        # violator_ids tetap ada biar tidak merusak struktur lama
        # tapi sekarang tidak dipakai untuk pewarnaan

        for b in boxes:
            x1, y1, x2, y2 = map(int, [b["x1"], b["y1"], b["x2"], b["y2"]])
            label = b["label"].lower()
            conf = b.get("confidence", 0.0)
            track_id = b.get("track_id")

            # 🟢 default hijau
            color = (0, 255, 0)

            # 🔴 kalau label termasuk violation → merah
            if label in VisualizerService.VIOLATION_LABELS:
                color = (0, 0, 255)

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