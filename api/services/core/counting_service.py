class CountingService:

    def count_boxes(self, boxes, labels=None):
        result = {}

        for b in boxes:
            label = b["label"].lower()

            # filter labels
            if labels and label not in labels:
                continue

            result[label] = result.get(label, 0) + 1

        return result



