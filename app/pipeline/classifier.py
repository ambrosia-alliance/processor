import pytorch_lightning as pl
from transformers import pipeline
from typing import List, Dict
import torch


class TherapyClassifier(pl.LightningModule):
    def __init__(self, model_name: str, categories: List[str], device: str = "cpu"):
        super().__init__()
        self.categories = categories
        self.device_name = device

        self.classifier = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=0 if device == "cuda" else -1
        )

    def classify_sentence(self, sentence: str) -> Dict[str, float]:
        result = self.classifier(sentence, self.categories, multi_label=False)

        label = result['labels'][0]
        score = result['scores'][0]

        return {
            "sentence": sentence,
            "category": label,
            "confidence": score
        }

    def classify_batch(self, sentences: List[str]) -> List[Dict[str, float]]:
        results = []
        for sentence in sentences:
            results.append(self.classify_sentence(sentence))
        return results

