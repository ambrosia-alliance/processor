from typing import List, Dict
from collections import defaultdict


class ResultAggregator:
    def __init__(self, categories: List[str]):
        self.categories = categories

    def aggregate(self, classifications: List[Dict[str, any]]) -> Dict[str, Dict]:
        category_data = defaultdict(lambda: {
            "count": 0,
            "total_confidence": 0.0,
            "sentences": []
        })

        for classification in classifications:
            category = classification["category"]
            confidence = classification["confidence"]
            sentence = classification["sentence"]

            category_data[category]["count"] += 1
            category_data[category]["total_confidence"] += confidence
            category_data[category]["sentences"].append({
                "text": sentence,
                "confidence": confidence
            })

        aggregated_results = {}
        for category in self.categories:
            if category in category_data:
                data = category_data[category]
                avg_confidence = data["total_confidence"] / data["count"]
                aggregated_results[category] = {
                    "count": data["count"],
                    "avg_confidence": round(avg_confidence, 4),
                    "sentences": data["sentences"]
                }
            else:
                aggregated_results[category] = {
                    "count": 0,
                    "avg_confidence": 0.0,
                    "sentences": []
                }

        return aggregated_results

