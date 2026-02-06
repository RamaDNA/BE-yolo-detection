import cv2

class DetectorService:
    def __init__(self, model, min_confidence=0.35):
        self.model = model
        self.min_confidence = min_confidence
    
    def detect_frame(self, frame):
        
        #convert OpenCV BGR -> RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = self.model(img_rgb)[0]

        boxes = []
        for box in result.boxes:
            conf = float(box.conf)
            if conf < self.min_confidence:
                continue

            cls = int(box.cls)
            label = self.model.names[cls].lower()

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            boxes.append({
                "label": label,
                "confidence": conf,
                "box":[int(x1), int(y1), int(x2), int(y2)]
            })
        
        return boxes