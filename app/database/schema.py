import sqlite3
from datetime import datetime
from typing import Optional


CREATE_SAMPLES_TABLE = """
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    labeled BOOLEAN DEFAULT 0
)
"""

CREATE_LABELS_TABLE = """
CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    is_positive BOOLEAN NOT NULL,
    confidence REAL,
    human_labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sample_id) REFERENCES samples(id),
    UNIQUE(sample_id, category)
)
"""

CREATE_TRAINING_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS training_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_path TEXT NOT NULL,
    metrics TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_samples_labeled ON samples(labeled)",
    "CREATE INDEX IF NOT EXISTS idx_labels_sample_id ON labels(sample_id)",
    "CREATE INDEX IF NOT EXISTS idx_labels_category ON labels(category)"
]


def initialize_database(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(CREATE_SAMPLES_TABLE)
    cursor.execute(CREATE_LABELS_TABLE)
    cursor.execute(CREATE_TRAINING_RUNS_TABLE)

    for index_sql in CREATE_INDEXES:
        cursor.execute(index_sql)

    conn.commit()
    conn.close()

