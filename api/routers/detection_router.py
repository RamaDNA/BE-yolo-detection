from fastapi import APIRouter, UploadFile
from services.core.model_loader import ModelLoader
from services.core.detector_service import DetectorService
from services.core.counting_service import CountingService

router = APIRouter()

model = ModelLoader.load()
detector = DetectorService(model)
counter = CountingService()

@router.post("/detect")
async def detect(file: UploadFile, labels: str = None , min_confidence: float = 0.35):

    img_bytes = await file.read()
    detector.min_confidence = min_confidence
    boxes = detector.detect(img_bytes)

    # ============ PARSE LABELS =============
    selected_labels = None
    if labels:
        selected_labels = [l.strip().lower() for l in labels.split(",")]
        selected_labels = [l for l in selected_labels if l]  # remove empty

    # ============ FILTER COUNTS =============
    counts = counter.count_boxes(boxes, labels=selected_labels)

    # ============ FILTER BOXES =============
    if selected_labels:
        boxes = [
            b for b in boxes
            if b["label"].lower() in selected_labels
        ]

    return {
        "counts": counts,
        "boxes": boxes
    }


