import sqlite3
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def add_sample(self, text: str, source: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO samples (text, source) VALUES (?, ?)",
            (text, source)
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_samples_batch(self, samples: List[Tuple[str, Optional[str]]]):
        cursor = self.conn.cursor()
        cursor.executemany(
            "INSERT INTO samples (text, source) VALUES (?, ?)",
            samples
        )
        self.conn.commit()

    def get_unlabeled_samples(self, limit: Optional[int] = None) -> List[Dict]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM samples WHERE labeled = 0 ORDER BY RANDOM()"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_sample_by_id(self, sample_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM samples WHERE id = ?", (sample_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def mark_sample_labeled(self, sample_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE samples SET labeled = 1 WHERE id = ?",
            (sample_id,)
        )
        self.conn.commit()

    def add_label(self, sample_id: int, category: str, is_positive: bool, confidence: Optional[float] = None):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO labels
               (sample_id, category, is_positive, confidence, human_labeled_at)
               VALUES (?, ?, ?, ?, ?)""",
            (sample_id, category, int(is_positive), confidence, datetime.now())
        )
        self.conn.commit()

    def get_labels_for_sample(self, sample_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM labels WHERE sample_id = ?",
            (sample_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_labeled_data(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.id, s.text, l.category, l.is_positive, l.confidence
            FROM samples s
            JOIN labels l ON s.id = l.sample_id
            WHERE s.labeled = 1
            ORDER BY s.id
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_label_statistics(self) -> Dict[str, Dict[str, int]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category,
                   SUM(CASE WHEN is_positive = 1 THEN 1 ELSE 0 END) as positive,
                   SUM(CASE WHEN is_positive = 0 THEN 1 ELSE 0 END) as negative
            FROM labels
            GROUP BY category
        """)

        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                'positive': row[1],
                'negative': row[2],
                'total': row[1] + row[2]
            }
        return stats

    def get_total_labeled_samples(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM samples WHERE labeled = 1")
        return cursor.fetchone()[0]

    def save_training_run(self, model_path: str, metrics: Dict) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO training_runs (model_path, metrics) VALUES (?, ?)",
            (model_path, json.dumps(metrics))
        )
        self.conn.commit()
        return cursor.lastrowid

    def delete_sample_and_labels(self, sample_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM labels WHERE sample_id = ?", (sample_id,))
        cursor.execute("DELETE FROM samples WHERE id = ?", (sample_id,))
        self.conn.commit()

