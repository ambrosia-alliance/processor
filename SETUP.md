# Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
./start_api.sh
```

Or manually:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the API

In a new terminal:

```bash
python example_usage.py
```

Or visit the interactive documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing the Pipeline Directly

To test the pipeline components without running the API:

```bash
python test_pipeline.py
```

## API Usage

### Classification Endpoint

```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Therapeutic Plasma Exchange showed 75% efficacy. The trial included 150 participants aged 40-65."
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

### List Categories

```bash
curl http://localhost:8000/categories
```

## Configuration

The pipeline can be configured via environment variables or the `.env` file:

- `MODEL_NAME`: HuggingFace model (default: facebook/bart-large-mnli)
- `CONFIDENCE_THRESHOLD`: Minimum confidence score (default: 0.5)
- `MIN_SENTENCE_LENGTH`: Minimum sentence length to process (default: 10)

## Project Structure

```
hackaging-processor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Configuration settings
│   └── pipeline/
│       ├── __init__.py
│       ├── chunker.py       # Sentence tokenization
│       ├── classifier.py    # BART-MNLI zero-shot classifier
│       └── aggregator.py    # Result aggregation
├── requirements.txt         # Python dependencies
├── README.md               # Documentation
├── SETUP.md               # This file
├── start_api.sh           # Quick start script
├── example_usage.py       # API usage example
└── test_pipeline.py       # Pipeline testing script
```

## Troubleshooting

### NLTK Data Error

If you see an error about missing NLTK data:

```python
import nltk
nltk.download('punkt')
```

### CUDA/GPU Issues

To force CPU usage, edit `.env`:

```
DEVICE=cpu
```

### Model Download

On first run, the model will be downloaded automatically. This may take a few minutes depending on your internet connection.

