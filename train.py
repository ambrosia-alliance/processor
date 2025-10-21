import argparse
import sys
from app.config import settings
from app.database.db import DatabaseManager
from app.training.trainer import TherapyTrainer
import json


def check_data_requirements(db_path: str) -> bool:
    with DatabaseManager(db_path) as db:
        stats = db.get_label_statistics()
        total_samples = db.get_total_labeled_samples()

    print(f"Total labeled samples: {total_samples}")
    print(f"\nLabels per category:")
    print(f"{'Category':<30} {'Positive':<10} {'Negative':<10} {'Total':<10}")
    print(f"{'-'*60}")

    insufficient = []
    for category in settings.categories:
        if category in stats:
            s = stats[category]
            print(f"{category:<30} {s['positive']:<10} {s['negative']:<10} {s['total']:<10}")

            if s['positive'] < settings.min_samples_per_category:
                insufficient.append((category, s['positive']))
        else:
            print(f"{category:<30} {0:<10} {0:<10} {0:<10}")
            insufficient.append((category, 0))

    print()

    if insufficient:
        print("WARNING: Some categories have fewer than minimum recommended samples:")
        for category, count in insufficient:
            print(f"  - {category}: {count} (need {settings.min_samples_per_category})")
        print()
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Train fine-tuned therapy classifier")
    parser.add_argument('--db', default=settings.db_path, help='Database path')
    parser.add_argument('--output-dir', default='models/finetuned', help='Output directory for model')
    parser.add_argument('--epochs', type=int, default=settings.training_epochs, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=settings.training_batch_size, help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=settings.training_learning_rate, help='Learning rate')
    parser.add_argument('--force', action='store_true', help='Skip data requirement check')

    args = parser.parse_args()

    print("="*80)
    print("Therapy Classifier Training")
    print("="*80)
    print()

    print("Checking data requirements...")
    sufficient = check_data_requirements(args.db)

    if not sufficient and not args.force:
        response = input("\nData requirements not met. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Training cancelled. Please collect more labels.")
            sys.exit(0)

    print("\nInitializing trainer...")
    trainer = TherapyTrainer(db_path=args.db, output_dir=args.output_dir)

    print(f"\nTraining configuration:")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.learning_rate}")
    print(f"  Focal loss alpha: {settings.focal_loss_alpha}")
    print(f"  Focal loss gamma: {settings.focal_loss_gamma}")
    print(f"  Device: {settings.device}")
    print()

    try:
        results = trainer.train(
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            warmup_steps=settings.training_warmup_steps,
            patience=settings.training_patience
        )

        print("\n" + "="*80)
        print("TRAINING RESULTS")
        print("="*80)
        print(f"\nModel saved to: {results['model_path']}")
        print("\nPer-category metrics:")

        for category in settings.categories:
            if category in results['metrics']:
                metrics = results['metrics'][category]
                print(f"\n{category}:")
                print(f"  Precision: {metrics['precision']:.4f}")
                print(f"  Recall: {metrics['recall']:.4f}")
                print(f"  F1-score: {metrics['f1-score']:.4f}")
                print(f"  Support: {metrics['support']}")

        print("\n" + "="*80)
        print(f"\nTo use this model, update app/config.py:")
        print(f"  finetuned_model_path = '{results['model_path']}'")
        print("="*80)

    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

