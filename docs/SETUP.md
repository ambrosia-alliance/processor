# Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Pipeline

```bash
python main.py
```

This will process a sample text and display the classification results.

### 3. Test Components

To test individual pipeline components:

```bash
python test_pipeline.py
```

## Using the Pipeline in Your Code

```python
from main import TherapyClassificationPipeline

pipeline = TherapyClassificationPipeline()

your_text = """
Therapeutic Plasma Exchange showed 75% efficacy.
The trial included 150 participants aged 40-65.
Side effects were mild.
"""

results = pipeline.process(your_text)

for category, data in results.items():
    if data["count"] > 0:
        print(f"\n{category}:")
        print(f"  Count: {data['count']}")
        print(f"  Avg Confidence: {data['avg_confidence']:.2%}")
        for sentence in data["sentences"]:
            print(f"  - {sentence['text']}")
```

## Configuration

Edit `app/config.py` to configure:

- `model_name`: HuggingFace model (default: facebook/bart-large-mnli)
- `device`: CUDA or CPU (auto-detected)
- `confidence_threshold`: Minimum confidence score (default: 0.5)
- `min_sentence_length`: Minimum sentence length to process (default: 10)

## Project Structure

```
hackaging-processor/
├── app/
│   ├── __init__.py
│   ├── config.py            # Configuration settings
│   └── pipeline/
│       ├── __init__.py
│       ├── chunker.py       # Sentence tokenization
│       ├── classifier.py    # BART-MNLI zero-shot classifier
│       └── aggregator.py    # Result aggregation
├── main.py                  # Main pipeline script
├── test_pipeline.py        # Component testing script
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
└── SETUP.md              # This file
```

## Troubleshooting

### NLTK Data Error

If you see an error about missing NLTK data:

```python
import nltk
nltk.download('punkt')
```

### CUDA/GPU Issues

To force CPU usage, edit `app/config.py`:

```python
device: str = "cpu"
```

### Model Download

On first run, the model will be downloaded automatically. This may take a few minutes depending on your internet connection.

