from typing import List, Optional
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
from app.database.db import DatabaseManager
from app.config import settings


class SampleCollector:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.chunker = SentenceChunker(min_length=settings.min_sentence_length)
        self.classifier = TherapyClassifier(
            model_name=settings.model_name,
            categories=settings.categories,
            device=settings.device,
            confidence_threshold=settings.confidence_threshold,
            max_categories=settings.max_categories_per_sentence,
            finetuned_model_path=settings.finetuned_model_path
        )

    def collect_from_text(self, text: str, source: Optional[str] = None) -> int:
        sentences = self.chunker.chunk(text)

        if not sentences:
            return 0

        classifications = self.classifier.classify_batch(sentences)

        samples = []
        for sentence in sentences:
            samples.append((sentence, source))

        with DatabaseManager(self.db_path) as db:
            db.add_samples_batch(samples)

        return len(samples)

    def collect_from_file(self, file_path: str) -> int:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        return self.collect_from_text(text, source=file_path)

