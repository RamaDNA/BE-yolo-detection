from PIL import Image
import io
import numpy as np

class DetectorService:
    # Constructor model conf min 70%
    def __init__(self, model , min_confidence=0.70):
        self.model = model
        self.min_confidence = min_confidence

    def detect(self, img_bytes):
        img = Image.open(io.BytesIO(img_bytes))
        result = self.model(img)[0]

        boxes = []
        for box in result.boxes:
            # count with confidence threshold
            conf = float(box.conf)
            if conf < self.min_confidence:
                continue
            
            cls = int(box.cls)
            label = self.model.names[cls].lower()   # <= paksa lowercase
            conf = float(box.conf)
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            boxes.append({
                "label": label,          # sudah lowercase
                "confidence": conf,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            })

        return boxes

    def track(self, frame):
        """
        Track objects in frame using ByteTrack
        """
        results = self.model.track(frame, persist=True, tracker="bytetrack.yaml")
        
        boxes = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    conf = float(box.conf)
                    if conf < self.min_confidence:
                        continue
                    
                    cls = int(box.cls)
                    label = self.model.names[cls].lower()
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    track_id = int(box.id) if box.id is not None else None
                    
                    boxes.append({
                        "label": label,
                        "confidence": conf,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "track_id": track_id
                    })
        print(f"[TRACK] boxes={len(boxes)}")
        return boxes
