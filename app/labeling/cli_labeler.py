import sys
import os
from typing import List, Dict, Optional
from app.database.db import DatabaseManager
from app.pipeline.classifier import TherapyClassifier
from app.config import settings


class CLILabeler:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = DatabaseManager(db_path)
        self.classifier = TherapyClassifier(
            model_name=settings.model_name,
            categories=settings.categories,
            device=settings.device,
            confidence_threshold=settings.confidence_threshold,
            max_categories=settings.max_categories_per_sentence,
            finetuned_model_path=settings.finetuned_model_path
        )
        self.undo_stack = []

    def start_labeling_session(self, batch_size: int = 50):
        self.db.connect()

        samples = self.db.get_unlabeled_samples(limit=batch_size)

        if not samples:
            print("\n🎉 No unlabeled samples found!")
            self._show_statistics()
            self.db.close()
            return

        print(f"\n{'='*80}")
        print(f"Starting labeling session with {len(samples)} samples")
        print(f"{'='*80}\n")

        print("Controls:")
        print("  y = Yes (positive)")
        print("  n = No (negative)")
        print("  s = Skip sample")
        print("  u = Undo last label")
        print("  q = Quit and save")
        print(f"\n{'='*80}\n")

        try:
            for idx, sample in enumerate(samples):
                result = self._label_sample(sample, idx + 1, len(samples))
                if result == 'quit':
                    break
                elif result == 'undo':
                    if self.undo_stack:
                        self._undo_last()
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Saving progress...")

        print(f"\n{'='*80}")
        print("Session complete!")
        print(f"{'='*80}\n")

        self._show_statistics()
        self.db.close()

    def _label_sample(self, sample: Dict, current: int, total: int) -> str:
        sample_id = sample['id']
        text = sample['text']

        predictions = self.classifier.classify_sentence(text)

        print(f"\n[{current}/{total}] Sample #{sample_id}")
        print(f"\nText: {text}\n")

        if predictions:
            print("Model predictions:")
            for pred in predictions:
                print(f"  - {pred['category']}: {pred['confidence']:.2%}")
            print()
        else:
            print("Model predictions: None\n")

        labels = {}

        for category in settings.categories:
            pred_conf = None
            for pred in predictions:
                if pred['category'] == category:
                    pred_conf = pred['confidence']
                    break

            prompt = f"  {category}"
            if pred_conf is not None:
                prompt += f" [predicted: {pred_conf:.2%}]"
            prompt += " (y/n/s/u/q): "

            while True:
                response = input(prompt).strip().lower()

                if response == 'q':
                    return 'quit'
                elif response == 'u':
                    return 'undo'
                elif response == 's':
                    return 'skip'
                elif response == 'y':
                    labels[category] = (True, pred_conf)
                    break
                elif response == 'n':
                    labels[category] = (False, pred_conf)
                    break
                else:
                    print("    Invalid input. Use y/n/s/u/q")

        for category, (is_positive, confidence) in labels.items():
            self.db.add_label(sample_id, category, is_positive, confidence)

        self.db.mark_sample_labeled(sample_id)

        self.undo_stack.append((sample_id, labels))

        return 'continue'

    def _undo_last(self):
        if not self.undo_stack:
            print("\nNothing to undo!\n")
            return

        sample_id, labels = self.undo_stack.pop()

        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM labels WHERE sample_id = ?", (sample_id,))
        cursor.execute("UPDATE samples SET labeled = 0 WHERE id = ?", (sample_id,))
        self.db.conn.commit()

        print(f"\nUndid labels for sample #{sample_id}\n")

    def _show_statistics(self):
        stats = self.db.get_label_statistics()
        total_samples = self.db.get_total_labeled_samples()

        print(f"Total labeled samples: {total_samples}\n")
        print("Labels per category:")
        print(f"{'Category':<30} {'Positive':<10} {'Negative':<10} {'Total':<10}")
        print(f"{'-'*60}")

        for category in settings.categories:
            if category in stats:
                s = stats[category]
                print(f"{category:<30} {s['positive']:<10} {s['negative']:<10} {s['total']:<10}")
            else:
                print(f"{category:<30} {0:<10} {0:<10} {0:<10}")

