from typing import Dict, List
from collections import defaultdict
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
import numpy as np
from datetime import datetime
from app.storage.database import LabelingDatabase
from app.storage.schemas import CategoryMetrics, LabeledSample
from app.config import settings


class AccuracyTracker:
    def __init__(self, database: LabelingDatabase = None):
        self.db = database or LabelingDatabase()
        self.categories = settings.categories

    def update_metrics(self, sample: LabeledSample):
        if not sample.human_label or not sample.ensemble_prediction:
            return

        category = sample.human_label

        labeled_samples = self.db.get_labeled_samples(category=category)

        if len(labeled_samples) == 0:
            return

        y_true = []
        y_pred = []

        for s in labeled_samples:
            y_true.append(s.human_label)
            y_pred.append(s.ensemble_prediction)

        metrics = self._calculate_metrics(category, y_true, y_pred)

        self.db.upsert_category_metrics(metrics)

    def _calculate_metrics(
        self,
        category: str,
        y_true: List[str],
        y_pred: List[str]
    ) -> CategoryMetrics:
        total_samples = len(y_true)

        category_true = [1 if label == category else 0 for label in y_true]
        category_pred = [1 if label == category else 0 for label in y_pred]

        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p and t == category)

        if sum(category_true) == 0:
            precision = 0.0
            recall = 0.0
            f1 = 0.0
        else:
            precision, recall, f1, _ = precision_recall_fscore_support(
                category_true,
                category_pred,
                average='binary',
                zero_division=0
            )

        accuracy = accuracy_score(y_true, y_pred)

        can_auto_accept = (
            total_samples >= settings.min_samples_for_handoff and
            accuracy >= settings.category_accuracy_threshold and
            not settings.human_review_enabled.get(category, True)
        )

        return CategoryMetrics(
            category=category,
            total_samples=total_samples,
            correct_predictions=correct,
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1),
            accuracy=float(accuracy),
            can_auto_accept=can_auto_accept,
            last_updated=datetime.now().isoformat()
        )

    def update_all_metrics(self):
        for category in self.categories:
            labeled_samples = self.db.get_labeled_samples(category=category)

            if not labeled_samples:
                continue

            y_true = [s.human_label for s in labeled_samples]
            y_pred = [s.ensemble_prediction for s in labeled_samples]

            metrics = self._calculate_metrics(category, y_true, y_pred)
            self.db.upsert_category_metrics(metrics)

    def can_auto_accept(self, category: str) -> bool:
        metrics = self.db.get_category_metrics(category)

        if not metrics:
            return False

        return metrics.can_auto_accept

    def should_review(self, prediction_result: Dict) -> bool:
        if prediction_result.get("needs_review", True):
            return True

        category = prediction_result.get("ensemble_prediction")
        if not category:
            return True

        if settings.human_review_enabled.get(category, True):
            if not self.can_auto_accept(category):
                return True

        return False

    def get_metrics_summary(self) -> Dict:
        all_metrics = self.db.get_all_metrics()

        summary = {
            "categories": {},
            "overall": {
                "total_labeled": 0,
                "auto_accept_enabled": 0,
                "needs_review": 0
            }
        }

        for category, metrics in all_metrics.items():
            summary["categories"][category] = metrics.to_dict()
            summary["overall"]["total_labeled"] += metrics.total_samples
            if metrics.can_auto_accept:
                summary["overall"]["auto_accept_enabled"] += 1

        summary["overall"]["needs_review"] = (
            len(self.categories) - summary["overall"]["auto_accept_enabled"]
        )

        return summary

    def enable_auto_accept(self, category: str):
        settings.human_review_enabled[category] = False
        self.update_all_metrics()

    def disable_auto_accept(self, category: str):
        settings.human_review_enabled[category] = True
        self.update_all_metrics()

    def get_category_report(self, category: str) -> Dict:
        metrics = self.db.get_category_metrics(category)

        if not metrics:
            return {
                "category": category,
                "status": "no_data",
                "message": "No labeled samples for this category yet"
            }

        samples_needed = max(0, settings.min_samples_for_handoff - metrics.total_samples)
        accuracy_gap = max(0, settings.category_accuracy_threshold - metrics.accuracy)

        status = "ready" if metrics.can_auto_accept else "needs_more_data"

        return {
            "category": category,
            "status": status,
            "metrics": metrics.to_dict(),
            "samples_needed": samples_needed,
            "accuracy_gap": round(accuracy_gap * 100, 2),
            "recommendation": self._get_recommendation(metrics, samples_needed, accuracy_gap)
        }

    def _get_recommendation(
        self,
        metrics: CategoryMetrics,
        samples_needed: int,
        accuracy_gap: float
    ) -> str:
        if metrics.can_auto_accept:
            return "Category is ready for auto-accept"

        if samples_needed > 0:
            return f"Need {samples_needed} more labeled samples"

        if accuracy_gap > 0:
            return f"Need {accuracy_gap*100:.1f}% accuracy improvement"

        return "Enable auto-accept in settings to activate"

