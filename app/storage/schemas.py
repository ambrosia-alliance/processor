"""
Data schemas for storing labeled samples and metrics.

This module defines dataclasses for representing labeled data, category metrics,
and synthetic prompts used throughout the labeling system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class LabeledSample:
    """
    Represents a labeled text sample with predictions and metadata.

    Supports multi-label classification where a sentence can have multiple
    category labels assigned by both models and humans.

    Attributes:
        id: Database primary key
        sentence: The text content
        human_labels: List of labels assigned by human reviewer
        model_predictions: Dictionary mapping model names to their predictions
        ensemble_predictions: List of labels selected by ensemble
        confidence: Average confidence score
        entropy: Prediction entropy (uncertainty measure)
        agreement_score: Model agreement metric
        needs_review: Whether human review is required
        timestamp: ISO format timestamp
        source: Data source ('synthetic' or 'real')
    """
    id: Optional[int] = None
    sentence: str = ""
    human_labels: List[str] = field(default_factory=list)
    model_predictions: Dict[str, List[str]] = field(default_factory=dict)
    ensemble_predictions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    entropy: float = 0.0
    agreement_scores: Dict[str, float] = field(default_factory=dict)
    needs_review: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "synthetic"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "sentence": self.sentence,
            "human_labels": self.human_labels,
            "model_predictions": self.model_predictions,
            "ensemble_predictions": self.ensemble_predictions,
            "confidence": self.confidence,
            "entropy": self.entropy,
            "agreement_scores": self.agreement_scores,
            "needs_review": self.needs_review,
            "timestamp": self.timestamp,
            "source": self.source
        }


@dataclass
class CategoryMetrics:
    """
    Tracks accuracy metrics for a specific category.

    Used to determine when a category is ready for automated classification
    based on historical accuracy.

    Attributes:
        category: Category name
        total_samples: Total number of labeled samples
        correct_predictions: Number of correct predictions
        precision: Precision score
        recall: Recall score
        f1_score: F1 score
        accuracy: Overall accuracy
        can_auto_accept: Whether category meets criteria for automation
        last_updated: ISO format timestamp of last update
    """
    category: str
    total_samples: int = 0
    correct_predictions: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    can_auto_accept: bool = False
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category,
            "total_samples": self.total_samples,
            "correct_predictions": self.correct_predictions,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "accuracy": self.accuracy,
            "can_auto_accept": self.can_auto_accept,
            "last_updated": self.last_updated
        }


@dataclass
class SyntheticPrompt:
    """
    Template for generating synthetic training data.

    Contains the prompt and examples used to generate realistic
    sentences for a specific category.

    Attributes:
        category: Category name
        prompt_template: Template text for LLM generation
        examples: Example sentences to guide generation
    """
    category: str
    prompt_template: str
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category,
            "prompt_template": self.prompt_template,
            "examples": self.examples
        }

