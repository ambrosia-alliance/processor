# Therapy Classification Pipeline

A Python ML pipeline that processes medical therapy text through zero-shot classification using BART-MNLI, returning aggregated category summaries.

## Features

- Sentence-level text chunking
- Zero-shot classification into 13 therapy-related categories
- Aggregated results with confidence scores
- PyTorch Lightning integration
- Simple Python interface

## Categories

The pipeline classifies text into the following categories:

- efficacy_extent
- efficacy_rate
- side_effect_severity
- side_effect_risk
- cost
- effect_size_evidence
- trial_design
- trial_length
- num_participants
- sex_participants
- age_range_participants
- other_participant_info
- other_study_info

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run the main pipeline:

```bash
python main.py
```

### Test individual components:

```bash
python test_pipeline.py
```

### Use in your own code:

```python
from main import TherapyClassificationPipeline

pipeline = TherapyClassificationPipeline()

text = """
Your therapy description text here...
"""

results = pipeline.process(text)

for category, data in results.items():
    if data["count"] > 0:
        print(f"{category}: {data['count']} sentences")
```

## Output Format

The pipeline returns a dictionary with categories as keys:

```python
{
  "efficacy_rate": {
    "count": 1,
    "avg_confidence": 0.92,
    "sentences": [
      {
        "text": "The therapeutic plasma exchange showed a 75% success rate.",
        "confidence": 0.92
      }
    ]
  },
  ...
}
```

## Configuration

Edit `app/config.py` to configure:

- `model_name`: HuggingFace model name
- `device`: CUDA or CPU
- `confidence_threshold`: Minimum confidence score
- `min_sentence_length`: Minimum sentence length to process

## Architecture

- **PyTorch Lightning**: ML model wrapper
- **BART-MNLI**: Zero-shot classification model
- **NLTK**: Sentence tokenization

