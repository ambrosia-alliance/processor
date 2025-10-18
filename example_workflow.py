from app.pipeline.synthetic_generator import SyntheticDataGenerator
from app.pipeline.ensemble_classifier import EnsembleClassifier
from app.pipeline.labeling_system import LabelingSystem
from app.pipeline.accuracy_tracker import AccuracyTracker
from app.storage.database import LabelingDatabase
from app.storage.schemas import LabeledSample
from app.config import settings


def demo_synthetic_generation():
    print("=" * 80)
    print("DEMO 1: Synthetic Data Generation")
    print("=" * 80)

    generator = SyntheticDataGenerator()

    categories = ["efficacy_rate", "cost", "side_effect_severity"]
    dataset = generator.generate_batch(categories, samples_per_category=3)

    for category, sentences in dataset.items():
        print(f"\n{category}:")
        for sentence in sentences:
            print(f"  - {sentence}")


def demo_ensemble_classification():
    print("\n" + "=" * 80)
    print("DEMO 2: Ensemble Classification")
    print("=" * 80)

    ensemble = EnsembleClassifier()

    test_sentences = [
        "The treatment achieved a 75% success rate in clinical trials.",
        "Mild fatigue occurred in approximately 15% of patients.",
        "Each session costs between $2,500 and $4,000."
    ]

    for sentence in test_sentences:
        result = ensemble.classify_sentence(sentence)
        print(f"\nSentence: {sentence}")
        print(f"Prediction: {result['ensemble_prediction']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Agreement: {result['agreement_score']:.2%}")
        print(f"Entropy: {result['entropy']:.3f}")
        print(f"Needs Review: {result['needs_review']}")


def demo_database_operations():
    print("\n" + "=" * 80)
    print("DEMO 3: Database Operations")
    print("=" * 80)

    db = LabelingDatabase()

    sample = LabeledSample(
        sentence="TPE demonstrated 80% efficacy in autoimmune patients.",
        ensemble_prediction="efficacy_rate",
        confidence=0.85,
        entropy=0.5,
        agreement_score=0.8,
        needs_review=False,
        source="demo"
    )

    sample_id = db.insert_sample(sample)
    print(f"\nInserted sample with ID: {sample_id}")

    retrieved = db.get_sample_by_id(sample_id)
    print(f"Retrieved: {retrieved.sentence}")

    stats = db.get_stats()
    print(f"\nDatabase stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def demo_accuracy_tracking():
    print("\n" + "=" * 80)
    print("DEMO 4: Accuracy Tracking")
    print("=" * 80)

    db = LabelingDatabase()
    tracker = AccuracyTracker(db)

    sample = LabeledSample(
        sentence="The study included 150 participants across multiple centers.",
        ensemble_prediction="num_participants",
        human_label="num_participants",
        confidence=0.90,
        entropy=0.3,
        agreement_score=1.0,
        needs_review=False,
        source="demo"
    )

    tracker.update_metrics(sample)

    report = tracker.get_category_report("num_participants")
    print(f"\nCategory Report:")
    print(f"  Status: {report['status']}")
    print(f"  Recommendation: {report['recommendation']}")


def demo_full_pipeline():
    print("\n" + "=" * 80)
    print("DEMO 5: Full Pipeline")
    print("=" * 80)

    print("\n1. Generate synthetic data")
    generator = SyntheticDataGenerator()
    dataset = generator.generate_batch(["efficacy_rate"], samples_per_category=2)
    print(f"   Generated {len(dataset['efficacy_rate'])} samples")

    print("\n2. Classify with ensemble")
    ensemble = EnsembleClassifier()
    db = LabelingDatabase()

    for sentence in dataset["efficacy_rate"]:
        result = ensemble.classify_sentence(sentence)
        sample = LabeledSample(
            sentence=result["sentence"],
            ensemble_prediction=result["ensemble_prediction"],
            confidence=result["confidence"],
            entropy=result["entropy"],
            agreement_score=result["agreement_score"],
            needs_review=result["needs_review"],
            source="synthetic"
        )
        sample_id = db.insert_sample(sample)
        print(f"   Classified: {sentence[:50]}...")
        print(f"   Prediction: {result['ensemble_prediction']} (needs review: {result['needs_review']})")

    print("\n3. Get samples needing review")
    samples = db.get_samples_needing_review(limit=5)
    print(f"   Found {len(samples)} samples needing review")

    print("\n4. View statistics")
    stats = db.get_stats()
    print(f"   Total samples: {stats['total_samples']}")
    print(f"   Needs review: {stats['needs_review']}")


def main():
    print("\n" + "=" * 80)
    print("ENSEMBLE LABELING SYSTEM - DEMONSTRATION")
    print("=" * 80)

    print("\nNote: Set NEBIUS_API_KEY environment variable to run synthetic generation.")
    print("This demo will skip synthetic generation if API key is not set.\n")

    import os
    if os.getenv("NEBIUS_API_KEY"):
        try:
            demo_synthetic_generation()
        except Exception as e:
            print(f"Synthetic generation demo skipped: {e}")
    else:
        print("Skipping synthetic generation demo (no API key)")

    try:
        demo_ensemble_classification()
    except Exception as e:
        print(f"Ensemble demo failed: {e}")

    try:
        demo_database_operations()
    except Exception as e:
        print(f"Database demo failed: {e}")

    try:
        demo_accuracy_tracking()
    except Exception as e:
        print(f"Accuracy tracking demo failed: {e}")

    try:
        demo_full_pipeline()
    except Exception as e:
        print(f"Full pipeline demo failed: {e}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python main.py generate --samples 10 --label")
    print("2. Run: python main.py label --batch-size 20")
    print("3. Run: python main.py stats")
    print("4. Run: python main.py auto-accept")
    print("\nSee USAGE.md for full documentation.")


if __name__ == "__main__":
    main()

