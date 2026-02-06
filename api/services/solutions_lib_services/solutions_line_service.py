from ultralytics import solutions

class SolutionsLineService:
    def __init__(self, region_points, model):
        self.counter = solutions.ObjectCounter(
            region=region_points,
            model=model,
            show=False
        )

    def update(self, frame):
        """
        Return:
            result.plot_im (frame annotated)
            result.counts (dict per object)
        """
        result = self.counter(frame)
        return result
