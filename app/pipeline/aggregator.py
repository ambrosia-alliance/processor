from typing import List, Dict
from collections import defaultdict


class ResultAggregator:
    def __init__(self, categories: List[str]):
        """
        Initialize the ResultAggregator with a fixed list of category names used for result aggregation.
        
        Parameters:
            categories (List[str]): Ordered list of category names that will be used as keys in the aggregated output; order is preserved.
        """
        self.categories = categories

    def aggregate(self, classifications: List[List[Dict[str, any]]]) -> Dict[str, Dict]:
        """
        Aggregate classification entries into per-category summaries.
        
        Parameters:
        	classifications (List[List[Dict[str, any]]]): Nested list where each inner list contains classification dicts for a sentence. Each classification dict must contain the keys `"category"` (str), `"confidence"` (float), and `"sentence"` (str).
        
        Returns:
        	aggregated_results (Dict[str, Dict]): Mapping from each category name (from self.categories) to a summary dict with:
        		- count (int): number of classification entries for the category
        		- avg_confidence (float): average confidence for the category rounded to 4 decimal places
        		- sentences (List[Dict[str, any]]): list of sentence entries, each with `"text"` (the sentence string) and `"confidence"` (the original confidence value)
        """
        category_data = defaultdict(lambda: {
            "count": 0,
            "total_confidence": 0.0,
            "sentences": []
        })

        for sentence_classifications in classifications:
            for classification in sentence_classifications:
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
