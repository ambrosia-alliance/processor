"""
Test script for multi-label ensemble classification.

This script tests the updated ensemble classifier with multi-label support.
"""

import sys
sys.path.insert(0, '/Users/andrewsoon/hackaging-processor')

from app.pipeline.ensemble_classifier import EnsembleClassifier
from app.config import settings


def test_multilabel_classification():
    """Test multi-label classification on sample sentences."""

    print("="*80)
    print("Multi-Label Ensemble Classifier Test")
    print("="*80)

    print(f"\nConfiguration:")
    print(f"  Label threshold: {settings.label_threshold}")
    print(f"  Supermajority threshold: {settings.supermajority_threshold}")
    print(f"  Entropy threshold: {settings.entropy_threshold}")

    print(f"\nLoading ensemble classifier...")
    ensemble = EnsembleClassifier(label_threshold=0.5)

    print(f"  Loaded {len(ensemble.classifiers)} models")

    test_sentences = [
        "TPE achieved 75% efficacy in trials with costs averaging $3000 per session.",
        "The study included 150 participants aged 35-70 years.",
        "Mild fatigue occurred in 15% of patients during the 12-month trial.",
        "Effect size analysis showed Cohen's d of 0.8 with 95% confidence interval.",
    ]

    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}:")
        print(f"{'='*80}")
        print(f"Sentence: {sentence}")
        print()

        result = ensemble.classify_sentence(sentence)

        print(f"Ensemble Predictions: {result['ensemble_predictions']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Entropy: {result['entropy']:.3f}")
        print(f"Needs Review: {result['needs_review']}")

        print(f"\nAgreement Scores:")
        for label, score in result['agreement_scores'].items():
            print(f"  {label}: {score:.2%}")

        print(f"\nModel Predictions:")
        for model, predictions in result['model_predictions'].items():
            model_name = model.split('/')[-1][:30]
            print(f"  {model_name}: {predictions}")

    print(f"\n{'='*80}")
    print("Test Complete")
    print("="*80)


if __name__ == "__main__":
    try:
        test_multilabel_classification()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

