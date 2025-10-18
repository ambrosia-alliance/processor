from app.config import settings
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
from app.pipeline.aggregator import ResultAggregator
import json
import os
import glob


class TherapyClassificationPipeline:
    def __init__(self, finetuned_model_path=None):
        self.chunker = SentenceChunker(min_length=settings.min_sentence_length)
        self.classifier = TherapyClassifier(
            model_name=settings.model_name,
            categories=settings.categories,
            device=settings.device,
            confidence_threshold=settings.confidence_threshold,
            max_categories=settings.max_categories_per_sentence,
            finetuned_model_path=finetuned_model_path
        )
        self.aggregator = ResultAggregator(categories=settings.categories)

    def process(self, text: str):
        sentences = self.chunker.chunk(text)

        if not sentences:
            return {"error": "No valid sentences found"}

        classifications = self.classifier.classify_batch(sentences)

        results = self.aggregator.aggregate(classifications)

        return results


def find_latest_finetuned_model():
    models_dir = "models/finetuned"
    if not os.path.exists(models_dir):
        return None

    model_dirs = glob.glob(os.path.join(models_dir, "model_*"))
    if not model_dirs:
        return None

    latest_model = max(model_dirs, key=os.path.getmtime)
    return latest_model


def print_results(results, title):
    print("=" * 80)
    print(title)
    print("=" * 80)

    for category, data in results.items():
        if data["count"] > 0:
            print(f"\n{category.upper().replace('_', ' ')}")
            print(f"  Count: {data['count']}")
            print(f"  Avg Confidence: {data['avg_confidence']:.2%}")
            print(f"  Sentences:")
            for sentence in data["sentences"]:
                print(f"    - {sentence['text'][:80]}...")
                print(f"      (confidence: {sentence['confidence']:.2%})")

    print("\n" + "=" * 80)


def compare_results(original_results, finetuned_results):
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    all_categories = set(original_results.keys()) | set(finetuned_results.keys())

    for category in sorted(all_categories):
        orig_count = original_results.get(category, {}).get('count', 0)
        ft_count = finetuned_results.get(category, {}).get('count', 0)

        if orig_count > 0 or ft_count > 0:
            print(f"\n{category}:")
            print(f"  Original Model: {orig_count} detections")
            print(f"  Finetuned Model: {ft_count} detections")

            if orig_count > 0 and ft_count > 0:
                orig_conf = original_results[category]['avg_confidence']
                ft_conf = finetuned_results[category]['avg_confidence']
                print(f"  Confidence Change: {orig_conf:.2%} → {ft_conf:.2%}")


def main():
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

    print("=" * 80)
    print("THERAPY CLASSIFICATION DEMO - MODEL COMPARISON")
    print("=" * 80)
    print(f"\nBase Model: {settings.model_name}")
    print(f"Device: {settings.device}")
    print()

    print("Running ORIGINAL MODEL (Zero-Shot)...")
    print()
    original_pipeline = TherapyClassificationPipeline(finetuned_model_path=None)
    original_results = original_pipeline.process(sample_text)
    print_results(original_results, "ORIGINAL MODEL RESULTS")

    finetuned_model_path = find_latest_finetuned_model()

    if finetuned_model_path:
        print(f"\nFound finetuned model: {finetuned_model_path}")
        print("\nRunning FINETUNED MODEL...")
        print()
        finetuned_pipeline = TherapyClassificationPipeline(finetuned_model_path=finetuned_model_path)
        finetuned_results = finetuned_pipeline.process(sample_text)
        print_results(finetuned_results, "FINETUNED MODEL RESULTS")

        compare_results(original_results, finetuned_results)
    else:
        print("\nNo finetuned model found. Run 'python train.py' to create one.")
        print("Original model results only shown above.")


if __name__ == "__main__":
    main()

