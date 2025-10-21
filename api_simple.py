from flask import Flask, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier

app = Flask(__name__)

chunker = None
classifier = None

def init_models():
    global chunker, classifier
    if chunker is None:
        print("Initializing models...")
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
        print("Models initialized!")

@app.route('/health', methods=['GET'])
def health():
    init_models()
    return jsonify({
        'status': 'healthy',
        'model': settings.model_name,
        'confidence_threshold': settings.confidence_threshold,
        'using_finetuned': classifier.use_finetuned if classifier else False,
        'device': settings.device
    })

@app.route('/classify', methods=['POST'])
def classify():
    init_models()

    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text field'}), 400

    text = data['text']
    if not text or not isinstance(text, str):
        return jsonify({'error': 'Text must be a non-empty string'}), 400

    sentences = chunker.chunk(text)
    if not sentences:
        return jsonify({'classifications': [], 'sentence_count': 0})

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

    return jsonify({
        'classifications': results,
        'sentence_count': len(sentences)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting API on port {port}")
    app.run(host='0.0.0.0', port=port, threaded=True)

