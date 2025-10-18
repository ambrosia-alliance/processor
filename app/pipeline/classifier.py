import pytorch_lightning as pl
from transformers import pipeline
from typing import List, Dict
import torch


class TherapyClassifier(pl.LightningModule):
    def __init__(self, model_name: str, categories: List[str], device: str = "cpu", confidence_threshold: float = 0.2, max_categories: int = 2):
        """
        Initialize the TherapyClassifier and configure a zero-shot classification pipeline.
        
        Parameters:
            model_name (str): Hugging Face model identifier used for zero-shot classification.
            categories (List[str]): List of candidate labels to classify input sentences against.
            device (str): "cuda" to use GPU (mapped to CUDA device 0), otherwise CPU is used.
            confidence_threshold (float): Minimum score (0.0–1.0) required for a label to be included in a sentence's results.
            max_categories (int): Maximum number of category entries to return per sentence.
        """
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
        """
        Return high-confidence category classifications for a single sentence.
        
        The classifier runs the configured zero-shot model in multi-label mode, filters labels whose scores are below the instance's `confidence_threshold`, and limits the number of returned categories to `max_categories`.
        
        Parameters:
            sentence (str): The text to classify.
        
        Returns:
            List[Dict[str, any]]: A list of classification dictionaries, each containing:
                - "sentence": the original sentence (str)
                - "category": the predicted category label (str)
                - "confidence": the model's confidence score for that label (float)
        """
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
        """
        Classify a list of sentences and return per-sentence classification results.
        
        Parameters:
            sentences (List[str]): Sentences to classify.
        
        Returns:
            List[List[Dict[str, any]]]: A list where each element corresponds to the classifications for the matching input sentence. Each classification is a dict with keys "sentence", "category", and "confidence".
        """
        results = []
        for sentence in sentences:
            results.append(self.classify_sentence(sentence))
        return results
