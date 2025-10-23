import sys
import json
from app.config import settings
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
import os

def classify_text(text: str):
    chunker = SentenceChunker(min_length=settings.min_sentence_length)

    finetuned_model_path = None
    if settings.finetuned_model_path and os.path.exists(settings.finetuned_model_path):
        finetuned_model_path = settings.finetuned_model_path

    classifier = TherapyClassifier(
        model_name=settings.model_name,
        categories=settings.categories,
        device=settings.device,
        confidence_threshold=settings.confidence_threshold,
        max_categories=settings.max_categories_per_sentence,
        finetuned_model_path=finetuned_model_path
    )

    sentences = chunker.chunk(text)

    if not sentences:
        return {
            'classifications': [],
            'sentence_count': 0
        }

    results = []
    for idx, sentence in enumerate(sentences):
        classifications = classifier.classify_sentence(sentence)

        for classification in classifications:
            results.append({
                'sentence': sentence,
                'sentence_idx': idx,
                'category': classification['category'],
                'confidence': float(classification['confidence'])
            })

    return {
        'classifications': results,
        'sentence_count': len(sentences)
    }

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--health':
        health_info = {
            'status': 'healthy',
            'model': settings.model_name,
            'confidence_threshold': settings.confidence_threshold,
            'device': settings.device
        }

        finetuned_model_path = None
        if settings.finetuned_model_path and os.path.exists(settings.finetuned_model_path):
            finetuned_model_path = settings.finetuned_model_path

        health_info['using_finetuned'] = finetuned_model_path is not None

        print(json.dumps(health_info))
        return

    text = sys.stdin.read()

    if not text or not text.strip():
        error_response = {'error': 'No text provided'}
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)

    try:
        result = classify_text(text)
        print(json.dumps(result))
    except Exception as e:
        error_response = {'error': str(e)}
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

