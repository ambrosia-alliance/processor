from flask import Flask, request, jsonify
from flask_cors import CORS
from app.config import settings
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
import os

app = Flask(__name__)
CORS(app)

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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model': settings.model_name,
        'confidence_threshold': settings.confidence_threshold,
        'using_finetuned': classifier.use_finetuned,
        'device': settings.device
    })

@app.route('/classify', methods=['POST'])
def classify():
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
                'confidence': classification['confidence']
            })

    return jsonify({
        'classifications': results,
        'sentence_count': len(sentences)
    })

if __name__ == '__main__':
    host = os.environ.get('API_HOST', settings.api_host)
    port = int(os.environ.get('API_PORT', settings.api_port))
    print(f"Starting processor API on {host}:{port}")
    print(f"Model: {settings.model_name}")
    print(f"Confidence threshold: {settings.confidence_threshold}")
    print(f"Using finetuned model: {classifier.use_finetuned}")
    app.run(host=host, port=port, debug=False)

