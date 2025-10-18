import sqlite3
import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from app.storage.schemas import LabeledSample, CategoryMetrics
from app.config import settings


class LabelingDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS labeled_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentence TEXT NOT NULL,
                    human_label TEXT,
                    model_predictions TEXT,
                    ensemble_prediction TEXT,
                    confidence REAL,
                    entropy REAL,
                    agreement_score REAL,
                    needs_review BOOLEAN,
                    timestamp TEXT,
                    source TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_metrics (
                    category TEXT PRIMARY KEY,
                    total_samples INTEGER,
                    correct_predictions INTEGER,
                    precision REAL,
                    recall REAL,
                    f1_score REAL,
                    accuracy REAL,
                    can_auto_accept BOOLEAN,
                    last_updated TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_human_label
                ON labeled_samples(human_label)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_needs_review
                ON labeled_samples(needs_review)
            """)

            conn.commit()

    def insert_sample(self, sample: LabeledSample) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO labeled_samples
                (sentence, human_label, model_predictions, ensemble_prediction,
                 confidence, entropy, agreement_score, needs_review, timestamp, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sample.sentence,
                sample.human_label,
                json.dumps(sample.model_predictions),
                sample.ensemble_prediction,
                sample.confidence,
                sample.entropy,
                sample.agreement_score,
                sample.needs_review,
                sample.timestamp,
                sample.source
            ))
            conn.commit()
            return cursor.lastrowid

    def update_sample(self, sample_id: int, human_label: str, needs_review: bool = False):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE labeled_samples
                SET human_label = ?, needs_review = ?
                WHERE id = ?
            """, (human_label, needs_review, sample_id))
            conn.commit()

    def get_samples_needing_review(self, limit: int = 10) -> List[LabeledSample]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM labeled_samples
                WHERE needs_review = 1
                ORDER BY entropy DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [self._row_to_sample(row) for row in rows]

    def get_labeled_samples(self, category: Optional[str] = None) -> List[LabeledSample]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if category:
                cursor.execute("""
                    SELECT * FROM labeled_samples
                    WHERE human_label = ? AND needs_review = 0
                """, (category,))
            else:
                cursor.execute("""
                    SELECT * FROM labeled_samples
                    WHERE human_label IS NOT NULL AND needs_review = 0
                """)

            rows = cursor.fetchall()
            return [self._row_to_sample(row) for row in rows]

    def get_sample_by_id(self, sample_id: int) -> Optional[LabeledSample]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM labeled_samples WHERE id = ?", (sample_id,))
            row = cursor.fetchone()
            return self._row_to_sample(row) if row else None

    def _row_to_sample(self, row) -> LabeledSample:
        return LabeledSample(
            id=row[0],
            sentence=row[1],
            human_label=row[2],
            model_predictions=json.loads(row[3]) if row[3] else {},
            ensemble_prediction=row[4],
            confidence=row[5],
            entropy=row[6],
            agreement_score=row[7],
            needs_review=bool(row[8]),
            timestamp=row[9],
            source=row[10]
        )

    def upsert_category_metrics(self, metrics: CategoryMetrics):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO category_metrics
                (category, total_samples, correct_predictions, precision, recall,
                 f1_score, accuracy, can_auto_accept, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.category,
                metrics.total_samples,
                metrics.correct_predictions,
                metrics.precision,
                metrics.recall,
                metrics.f1_score,
                metrics.accuracy,
                metrics.can_auto_accept,
                metrics.last_updated
            ))
            conn.commit()

    def get_category_metrics(self, category: str) -> Optional[CategoryMetrics]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM category_metrics WHERE category = ?
            """, (category,))
            row = cursor.fetchone()

            if row:
                return CategoryMetrics(
                    category=row[0],
                    total_samples=row[1],
                    correct_predictions=row[2],
                    precision=row[3],
                    recall=row[4],
                    f1_score=row[5],
                    accuracy=row[6],
                    can_auto_accept=bool(row[7]),
                    last_updated=row[8]
                )
            return None

    def get_all_metrics(self) -> Dict[str, CategoryMetrics]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM category_metrics")
            rows = cursor.fetchall()

            return {
                row[0]: CategoryMetrics(
                    category=row[0],
                    total_samples=row[1],
                    correct_predictions=row[2],
                    precision=row[3],
                    recall=row[4],
                    f1_score=row[5],
                    accuracy=row[6],
                    can_auto_accept=bool(row[7]),
                    last_updated=row[8]
                )
                for row in rows
            }

    def export_training_data(self, output_path: str):
        samples = self.get_labeled_samples()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            for sample in samples:
                f.write(json.dumps({
                    "text": sample.sentence,
                    "label": sample.human_label
                }) + "\n")

    def get_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM labeled_samples")
            total_samples = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM labeled_samples WHERE human_label IS NOT NULL")
            labeled_samples = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM labeled_samples WHERE needs_review = 1")
            needs_review = cursor.fetchone()[0]

            return {
                "total_samples": total_samples,
                "labeled_samples": labeled_samples,
                "needs_review": needs_review,
                "unlabeled_samples": total_samples - labeled_samples
            }

