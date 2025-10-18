import argparse
import json
from app.config import settings
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
from app.pipeline.aggregator import ResultAggregator
from app.pipeline.synthetic_generator import SyntheticDataGenerator
from app.pipeline.ensemble_classifier import EnsembleClassifier
from app.pipeline.labeling_system import LabelingSystem
from app.pipeline.accuracy_tracker import AccuracyTracker
from app.storage.database import LabelingDatabase
from app.storage.schemas import LabeledSample


class TherapyClassificationPipeline:
    def __init__(self):
        self.chunker = SentenceChunker(min_length=settings.min_sentence_length)
        self.classifier = TherapyClassifier(
            model_name=settings.model_name,
            categories=settings.categories,
            device=settings.device
        )
        self.aggregator = ResultAggregator(categories=settings.categories)

    def process(self, text: str):
        sentences = self.chunker.chunk(text)

        if not sentences:
            return {"error": "No valid sentences found"}

        classifications = self.classifier.classify_batch(sentences)

        results = self.aggregator.aggregate(classifications)

        return results


class EnsemblePipeline:
    def __init__(self):
        self.chunker = SentenceChunker(min_length=settings.min_sentence_length)
        self.ensemble = EnsembleClassifier()
        self.db = LabelingDatabase()
        self.tracker = AccuracyTracker(self.db)

    def process(self, text: str, auto_accept: bool = False):
        sentences = self.chunker.chunk(text)

        if not sentences:
            return {"error": "No valid sentences found"}

        classifications = self.ensemble.classify_batch(sentences)

        for classification in classifications:
            sample = LabeledSample(
                sentence=classification["sentence"],
                ensemble_prediction=classification["ensemble_prediction"],
                confidence=classification["confidence"],
                entropy=classification["entropy"],
                agreement_score=classification["agreement_score"],
                model_predictions=classification["model_predictions"],
                needs_review=classification["needs_review"],
                source="real"
            )

            if auto_accept and not self.tracker.should_review(classification):
                sample.human_label = sample.ensemble_prediction
                sample.needs_review = False

            self.db.insert_sample(sample)

        return {
            "processed": len(classifications),
            "needs_review": sum(1 for c in classifications if c["needs_review"]),
            "auto_accepted": sum(1 for c in classifications if not c["needs_review"])
        }


def mode_generate_synthetic(args):
    print("Generating synthetic data...")
    generator = SyntheticDataGenerator()

    if args.categories:
        categories = args.categories.split(",")
        dataset = generator.generate_batch(categories, args.samples)
    else:
        dataset = generator.generate_balanced_dataset(args.samples)

    print(f"\nGenerated {sum(len(v) for v in dataset.values())} samples")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(dataset, f, indent=2)
        print(f"Saved to {args.output}")

    if args.label:
        labeling_system = LabelingSystem()
        labeling_system.bulk_label_synthetic(dataset)
        print("Added to database for labeling")


def mode_label(args):
    labeling_system = LabelingSystem()
    labeling_system.start_labeling_session(batch_size=args.batch_size)


def mode_classify(args):
    if args.ensemble:
        pipeline = EnsemblePipeline()
    else:
        pipeline = TherapyClassificationPipeline()

    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        text = """
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

    results = pipeline.process(text, auto_accept=args.auto_accept)

    print("\nResults:")
    print(json.dumps(results, indent=2))


def mode_stats(args):
    labeling_system = LabelingSystem()

    labeling_system.display_stats()
    print()
    labeling_system.display_metrics()

    if args.category:
        print()
        labeling_system.display_category_report(args.category)


def mode_export(args):
    db = LabelingDatabase()
    output_path = args.output or settings.export_path + "training_data.jsonl"
    db.export_training_data(output_path)
    print(f"Exported training data to {output_path}")


def mode_auto_accept(args):
    labeling_system = LabelingSystem()
    labeling_system.auto_accept_ready_categories()


def main():
    parser = argparse.ArgumentParser(
        description="Therapy Classification Pipeline with Ensemble Learning and Human-in-the-Loop"
    )

    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    generate_parser = subparsers.add_parser("generate", help="Generate synthetic training data")
    generate_parser.add_argument("--samples", type=int, default=10, help="Samples per category")
    generate_parser.add_argument("--categories", type=str, help="Comma-separated categories")
    generate_parser.add_argument("--output", type=str, help="Output JSON file")
    generate_parser.add_argument("--label", action="store_true", help="Add to database for labeling")

    label_parser = subparsers.add_parser("label", help="Start labeling session")
    label_parser.add_argument("--batch-size", type=int, default=10, help="Samples per session")

    classify_parser = subparsers.add_parser("classify", help="Classify text")
    classify_parser.add_argument("--text", type=str, help="Text to classify")
    classify_parser.add_argument("--file", type=str, help="File to classify")
    classify_parser.add_argument("--ensemble", action="store_true", help="Use ensemble classifier")
    classify_parser.add_argument("--auto-accept", action="store_true", help="Auto-accept low entropy predictions")

    stats_parser = subparsers.add_parser("stats", help="Show statistics and metrics")
    stats_parser.add_argument("--category", type=str, help="Show detailed report for category")

    export_parser = subparsers.add_parser("export", help="Export training data")
    export_parser.add_argument("--output", type=str, help="Output file path")

    subparsers.add_parser("auto-accept", help="Check and enable auto-accept for ready categories")

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return

    if args.mode == "generate":
        mode_generate_synthetic(args)
    elif args.mode == "label":
        mode_label(args)
    elif args.mode == "classify":
        mode_classify(args)
    elif args.mode == "stats":
        mode_stats(args)
    elif args.mode == "export":
        mode_export(args)
    elif args.mode == "auto-accept":
        mode_auto_accept(args)


if __name__ == "__main__":
    main()

