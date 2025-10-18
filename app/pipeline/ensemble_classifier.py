from transformers import pipeline
from typing import List, Dict, Tuple, Set
import numpy as np
from scipy.stats import entropy
from collections import Counter, defaultdict
from app.config import settings


class EnsembleClassifier:
    """
    Multi-label ensemble classifier using multiple zero-shot models.

    Runs parallel classification across multiple models, aggregates predictions
    using supermajority voting, and identifies high-uncertainty cases for human review.

    Attributes:
        model_names: List of HuggingFace model identifiers
        device: Computing device ('cuda' or 'cpu')
        categories: List of classification categories
        classifiers: Dictionary of loaded transformer pipelines
    """
    def __init__(self, model_names: List[str] = None, device: str = None, label_threshold: float = 0.5):
        """
        Initialize the ensemble classifier.

        Args:
            model_names: List of model identifiers to use in ensemble
            device: Computing device ('cuda' or 'cpu')
            label_threshold: Minimum score for a label to be accepted (multi-label)
        """
        self.model_names = model_names or settings.ensemble_models
        self.device = device or settings.device
        self.categories = settings.categories
        self.label_threshold = label_threshold
        self.classifiers = self._load_classifiers()

    def _load_classifiers(self) -> Dict[str, any]:
        """
        Load all transformer models into memory.

        Returns:
            Dictionary mapping model names to pipeline objects
        """
        classifiers = {}
        device_id = 0 if self.device == "cuda" else -1

        for model_name in self.model_names:
            try:
                print(f"Loading model: {model_name}")
                classifiers[model_name] = pipeline(
                    "zero-shot-classification",
                    model=model_name,
                    device=device_id
                )
            except Exception as e:
                print(f"Warning: Could not load {model_name}: {e}")
                continue

        if not classifiers:
            raise RuntimeError("No models could be loaded successfully")

        return classifiers

    def classify_sentence(self, sentence: str) -> Dict:
        """
        Classify a sentence using all models in the ensemble.

        Supports multi-label classification where a sentence can belong to
        multiple categories if scores exceed the threshold.

        Args:
            sentence: Input text to classify

        Returns:
            Dictionary containing:
                - sentence: Original input text
                - ensemble_predictions: List of predicted labels
                - confidence: Average confidence across models
                - entropy: Prediction entropy (uncertainty measure)
                - agreement_score: Proportion of models agreeing
                - model_predictions: Individual model predictions
                - model_scores: Detailed scores from each model
                - needs_review: Whether human review is needed
        """
        model_predictions = {}
        model_scores = {}

        for model_name, classifier in self.classifiers.items():
            try:
                result = classifier(sentence, self.categories, multi_label=True)

                predicted_labels = [
                    label for label, score in zip(result['labels'], result['scores'])
                    if score >= self.label_threshold
                ]

                if not predicted_labels:
                    predicted_labels = [result['labels'][0]]

                model_predictions[model_name] = predicted_labels
                model_scores[model_name] = {
                    label: score
                    for label, score in zip(result['labels'], result['scores'])
                }
            except Exception as e:
                print(f"Error with model {model_name}: {e}")
                continue

        if not model_predictions:
            return self._create_empty_result(sentence)

        ensemble_predictions, agreement_scores = self._vote_multilabel(model_predictions)

        avg_confidence = self._calculate_average_confidence_multilabel(
            model_scores, ensemble_predictions
        )

        prediction_entropy = self._calculate_entropy_multilabel(model_predictions)

        return {
            "sentence": sentence,
            "ensemble_predictions": ensemble_predictions,
            "confidence": avg_confidence,
            "entropy": prediction_entropy,
            "agreement_scores": agreement_scores,
            "model_predictions": model_predictions,
            "model_scores": model_scores,
            "needs_review": self._needs_review_multilabel(agreement_scores, prediction_entropy)
        }

    def _vote_multilabel(self, predictions: Dict[str, List[str]]) -> Tuple[List[str], Dict[str, float]]:
        """
        Aggregate multi-label predictions using supermajority voting.

        Args:
            predictions: Dictionary of model name to list of predicted labels

        Returns:
            Tuple of (selected labels, agreement scores per label)
        """
        label_votes = defaultdict(int)
        total_models = len(predictions)

        for model_name, labels in predictions.items():
            for label in labels:
                label_votes[label] += 1

        selected_labels = []
        agreement_scores = {}

        for label, count in label_votes.items():
            agreement = count / total_models
            agreement_scores[label] = agreement

            if agreement >= settings.supermajority_threshold:
                selected_labels.append(label)

        if not selected_labels:
            most_common_label = max(label_votes.items(), key=lambda x: x[1])[0]
            selected_labels = [most_common_label]
            agreement_scores[most_common_label] = label_votes[most_common_label] / total_models

        return selected_labels, agreement_scores

    def _calculate_average_confidence_multilabel(
        self,
        model_scores: Dict[str, Dict[str, float]],
        predicted_labels: List[str]
    ) -> float:
        """
        Calculate average confidence across all selected labels.

        Args:
            model_scores: Scores from each model for all categories
            predicted_labels: Labels selected by ensemble

        Returns:
            Average confidence score
        """
        confidences = []
        for label in predicted_labels:
            for model_name, scores in model_scores.items():
                if label in scores:
                    confidences.append(scores[label])

        return np.mean(confidences) if confidences else 0.0

    def _calculate_entropy_multilabel(self, predictions: Dict[str, List[str]]) -> float:
        """
        Calculate entropy across all label predictions.

        Higher entropy indicates more disagreement/uncertainty.

        Args:
            predictions: Dictionary of model predictions

        Returns:
            Entropy value
        """
        label_counts = defaultdict(int)
        total_predictions = 0

        for model_name, labels in predictions.items():
            for label in labels:
                label_counts[label] += 1
                total_predictions += 1

        if total_predictions == 0:
            return 0.0

        probabilities = [count / total_predictions for count in label_counts.values()]

        return float(entropy(probabilities, base=2))

    def _needs_review_multilabel(self, agreement_scores: Dict[str, float], prediction_entropy: float) -> bool:
        """
        Determine if sample needs human review based on agreement and entropy.

        Args:
            agreement_scores: Agreement scores per label
            prediction_entropy: Overall prediction entropy

        Returns:
            True if human review is needed
        """
        if not agreement_scores:
            return True

        min_agreement = min(agreement_scores.values())
        if min_agreement < settings.supermajority_threshold:
            return True

        if prediction_entropy > settings.entropy_threshold:
            return True

        return False

    def _create_empty_result(self, sentence: str) -> Dict:
        """
        Create an empty result when classification fails.

        Args:
            sentence: Input sentence

        Returns:
            Empty result dictionary
        """
        return {
            "sentence": sentence,
            "ensemble_predictions": [],
            "confidence": 0.0,
            "entropy": 0.0,
            "agreement_scores": {},
            "model_predictions": {},
            "model_scores": {},
            "needs_review": True
        }

    def classify_batch(self, sentences: List[str]) -> List[Dict]:
        """
        Classify multiple sentences in batch.

        Args:
            sentences: List of input sentences

        Returns:
            List of classification results
        """
        results = []
        for sentence in sentences:
            result = self.classify_sentence(sentence)
            results.append(result)
        return results

    def get_model_info(self) -> Dict:
        """
        Get information about the ensemble configuration.

        Returns:
            Dictionary with model count, names, and thresholds
        """
        return {
            "num_models": len(self.classifiers),
            "models": list(self.classifiers.keys()),
            "supermajority_threshold": settings.supermajority_threshold,
            "entropy_threshold": settings.entropy_threshold
        }

