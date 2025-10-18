from app.config import settings
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
from app.pipeline.aggregator import ResultAggregator
import json


class TherapyClassificationPipeline:
    def __init__(self):
        self.chunker = SentenceChunker(min_length=settings.min_sentence_length)
        self.classifier = TherapyClassifier(
            model_name=settings.model_name,
            categories=settings.categories,
            device=settings.device,
            confidence_threshold=settings.confidence_threshold,
            max_categories=settings.max_categories_per_sentence
        )
        self.aggregator = ResultAggregator(categories=settings.categories)

    def process(self, text: str):
        sentences = self.chunker.chunk(text)

        if not sentences:
            return {"error": "No valid sentences found"}

        classifications = self.classifier.classify_batch(sentences)

        results = self.aggregator.aggregate(classifications)

        return results


def main():
    print("Initializing Therapy Classification Pipeline...")
    print(f"Model: {settings.model_name}")
    print(f"Device: {settings.device}")
    print()

    pipeline = TherapyClassificationPipeline()

    sample_text = """
    Therapeutic Plasma Exchange (TPE) has demonstrated a 75% efficacy rate in treating autoimmune conditions.
    The treatment showed significant improvement in patient outcomes over a 6-month period.
    Common side effects include mild fatigue and temporary dizziness, occurring in approximately 15% of cases.
    The average cost per session is $2,500 to $4,000.
    This double-blind randomized controlled trial included 150 participants.
    The study population consisted of 60% female and 40% male participants.
    Participants ranged in age from 35 to 70 years old.
    The trial was conducted over a 12-month period with a 6-month follow-up.
    Effect size analysis showed a Cohen's d of 0.8, indicating a large treatment effect.
    """

    print("Processing sample text...")
    print()

    results = pipeline.process(sample_text)

    print("=" * 80)
    print("CLASSIFICATION RESULTS")
    print("=" * 80)

    for category, data in results.items():
        if data["count"] > 0:
            print(f"\n{category.upper().replace('_', ' ')}")
            print(f"  Count: {data['count']}")
            print(f"  Avg Confidence: {data['avg_confidence']:.2%}")
            print(f"  Sentences:")
            for sentence in data["sentences"]:
                print(f"    - {sentence['text']}")
                print(f"      (confidence: {sentence['confidence']:.2%})")

    print("\n" + "=" * 80)

    print("\nJSON Output:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

