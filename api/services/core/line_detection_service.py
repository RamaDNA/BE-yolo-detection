import math

class SimpleTracker:
    def __init__(self, max_lost=20):
        self.next_id = 1
        self.tracks = {}  # id → {"centroid": (x,y), "lost": int}
        self.max_lost = max_lost

    def update(self, detections):
        # detections: list → {x1,y1,x2,y2,label}
        centroids = []
        for det in detections:
            cx = int((det["x1"] + det["x2"]) / 2)
            cy = int((det["y1"] + det["y2"]) / 2)
            centroids.append((cx, cy, det))

        updated = {}

        # MATCH existing IDs
        for tid, info in self.tracks.items():
            (px, py) = info["centroid"]

            min_det = None
            min_dist = 1e9

            for c in centroids:
                cx, cy, det = c
                dist = math.hypot(cx - px, cy - py)
                if dist < min_dist:
                    min_dist = dist
                    min_det = c

            if min_det and min_dist < 60:
                cx, cy, det = min_det
                updated[tid] = {"centroid": (cx, cy), "det": det, "lost": 0}
                centroids.remove(min_det)
            else:
                info["lost"] += 1
                if info["lost"] < self.max_lost:
                    updated[tid] = info

        # NEW IDS
        for c in centroids:
            cx, cy, det = c
            updated[self.next_id] = {"centroid": (cx, cy), "det": det, "lost": 0}
            self.next_id += 1

        self.tracks = updated
        return updated


class LineDetectionService:
    def __init__(self, p1, p2, target_labels=None):
        self.p1 = p1
        self.p2 = p2
        self.target_labels = target_labels or []

        self.previous_centers = {}   # track_id → (x,y)
        self.crossed = set()         # anti double count

        self.in_count = 0
        self.out_count = 0

    def _line_side(self, point):
        (x1, y1), (x2, y2) = self.p1, self.p2
        x, y = point
        return (x - x1)*(y2 - y1) - (y - y1)*(x2 - x1)

    def update(self, boxes):
        for b in boxes:
            if b.get("track_id") is None:
                continue
            if b["label"].lower() not in self.target_labels:
                continue

            tid = b["track_id"]
            cx = int((b["x1"] + b["x2"]) / 2)
            cy = int((b["y1"] + b["y2"]) / 2)
            center = (cx, cy)

            if tid in self.previous_centers and tid not in self.crossed:
                prev_center = self.previous_centers[tid]

                prev_side = self._line_side(prev_center)
                curr_side = self._line_side(center)

                # IN
                if prev_side < 0 and curr_side > 0:
                    self.in_count += 1
                    self.crossed.add(tid)

                # OUT
                elif prev_side > 0 and curr_side < 0:
                    self.out_count += 1
                    self.crossed.add(tid)

            self.previous_centers[tid] = center

        return {
            "in": self.in_count,
            "out": self.out_count,
            "current_inside": self.in_count - self.out_count
        }



# class LineDetectionService:
#     def __init__(self, p1, p2, target_labels=None):
#         self.p1 = p1
#         self.p2 = p2
#         self.target_labels = target_labels

#         self.tracker = SimpleTracker(max_lost=10)

#         self.previous_centers = {}   # track_id → (x,y)
#         self.in_count = 0
#         self.out_count = 0

#     def _line_side(self, point):
#         (x1, y1), (x2, y2) = self.p1, self.p2
#         x, y = point
#         return (x - x1)*(y2 - y1) - (y - y1)*(x2 - x1)

#     def update(self, boxes):
#         # Filter hanya label yang mau dihitung
#         boxes = [b for b in boxes if b["label"].lower() in self.target_labels]

#         tracked = self.tracker.update(boxes)

#         for tid, info in tracked.items():
#             center = info["centroid"]

#             # ada history center sebelumnya
#             if tid in self.previous_centers:
#                 prev_center = self.previous_centers[tid]

#                 prev_side = self._line_side(prev_center)
#                 curr_side = self._line_side(center)

#                 # crossing dari atas → bawah (kalo vertical dari kiri ke kanan == IN)
#                 # #function IN
#                 # if prev_side < 0 and curr_side > 0:
#                 #     self.in_count += 1

#                 # # crossing dari bawah → atas
#                 # #function OUT
#                 # elif prev_side > 0 and curr_side < 0:
#                 #     self.out_count += 1

#                 # crossing dari kanan → kiri (IN)
#                 if prev_side > 0 and curr_side < 0:
#                     self.in_count += 1

#                 # crossing dari kiri → kanan (OUT)
#                 elif prev_side < 0 and curr_side > 0:
#                     self.out_count += 1

#             self.previous_centers[tid] = center

#         return {
#             "in": self.in_count,
#             "out": self.out_count,
#             "current_inside": self.in_count - self.out_count
#         }
