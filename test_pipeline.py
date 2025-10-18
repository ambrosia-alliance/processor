from app.config import settings
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
from app.pipeline.aggregator import ResultAggregator


def test_pipeline():
    print("Testing ML Classification Pipeline\n")
    print("=" * 80)

    sample_text = """
    Therapeutic Plasma Exchange has shown a 75% success rate.
    The treatment costs approximately $3,000 per session.
    Side effects were mild and included temporary fatigue.
    The trial included 120 participants aged 40-65 years.
    This was a randomized controlled trial lasting 6 months.
    """

    print("\n1. Initializing components...")
    chunker = SentenceChunker(min_length=settings.min_sentence_length)
    classifier = TherapyClassifier(
        model_name=settings.model_name,
        categories=settings.categories,
        device=settings.device
    )
    aggregator = ResultAggregator(categories=settings.categories)
    print(f"   Model: {settings.model_name}")
    print(f"   Device: {settings.device}")
    print(f"   Categories: {len(settings.categories)}")

    print("\n2. Chunking text into sentences...")
    sentences = chunker.chunk(sample_text)
    print(f"   Found {len(sentences)} sentences")
    for i, sentence in enumerate(sentences, 1):
        print(f"   {i}. {sentence}")

    print("\n3. Classifying sentences...")
    classifications = classifier.classify_batch(sentences)
    for i, result in enumerate(classifications, 1):
        print(f"   {i}. {result['category']} (confidence: {result['confidence']:.2%})")

    print("\n4. Aggregating results...")
    aggregated = aggregator.aggregate(classifications)

    print("\n5. Final Results:")
    print("-" * 80)
    for category, data in aggregated.items():
        if data["count"] > 0:
            print(f"\n{category}:")
            print(f"  Count: {data['count']}")
            print(f"  Avg Confidence: {data['avg_confidence']:.2%}")
            for sentence in data["sentences"]:
                print(f"  - {sentence['text']}")

    print("\n" + "=" * 80)
    print("Pipeline test complete!")


if __name__ == "__main__":
    test_pipeline()

