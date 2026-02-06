from ultralytics import solutions

class SolutionsRegionService:
    def __init__(self, region_points, model):
        self.region = solutions.RegionCounter(
            region=region_points,
            model=model,
            show=False
        )

    def update(self, frame):
        result = self.region(frame)
        return result
