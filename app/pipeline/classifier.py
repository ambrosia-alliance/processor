import pytorch_lightning as pl
from transformers import pipeline
from typing import List, Dict
import torch


class TherapyClassifier(pl.LightningModule):
    def __init__(self, model_name: str, categories: List[str], device: str = "cpu", confidence_threshold: float = 0.2, max_categories: int = 2):
        super().__init__()
        self.categories = categories
        self.device_name = device
        self.confidence_threshold = confidence_threshold
        self.max_categories = max_categories

        self.classifier = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=0 if device == "cuda" else -1
        )

    def classify_sentence(self, sentence: str) -> List[Dict[str, any]]:
        result = self.classifier(sentence, self.categories, multi_label=True)

        classifications = []
        for label, score in zip(result['labels'], result['scores']):
            if score >= self.confidence_threshold and len(classifications) < self.max_categories:
                classifications.append({
                    "sentence": sentence,
                    "category": label,
                    "confidence": score
                })

        return classifications

    def classify_batch(self, sentences: List[str]) -> List[List[Dict[str, any]]]:
        results = []
        for sentence in sentences:
            results.append(self.classify_sentence(sentence))
        return results

