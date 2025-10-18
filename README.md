# Therapy Classification Pipeline

A Python ML pipeline that processes medical therapy text through zero-shot classification using BART-MNLI, returning aggregated category summaries. Includes human-in-the-loop labeling and fine-tuning capabilities with focal loss.

## Features

- Sentence-level text chunking
- Zero-shot classification into 13 therapy-related categories
- Aggregated results with confidence scores
- Human-in-the-loop labeling system with CLI interface
- Fine-tuning with focal loss (penalizes false positives)
- SQLite-based label storage
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

### Fine-tune the model with your own labels:

See [FINE_TUNING_GUIDE.md](FINE_TUNING_GUIDE.md) for detailed instructions.

**Quick start:**

1. Label samples:
```bash
python label.py sample_data.txt
```

2. Train model (after ~500+ labeled samples):
```bash
python train.py
```

3. Update `app/config.py` with the trained model path and run the pipeline

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

- `model_name`: HuggingFace model name (default: facebook/bart-large-mnli)
- `device`: CUDA or CPU
- `confidence_threshold`: Minimum confidence score (default: 0.2)
- `min_sentence_length`: Minimum sentence length to process
- `finetuned_model_path`: Path to fine-tuned model (default: None)
- `focal_loss_alpha`: False positive penalty weight (default: 0.75)
- `focal_loss_gamma`: Hard example focus (default: 2.0)

## Architecture

- **PyTorch Lightning**: ML model wrapper
- **BART-MNLI**: Zero-shot classification model
- **Focal Loss**: Penalizes false positives (α=0.75) for fine-tuning
- **SQLite**: Label storage and training data management
- **NLTK**: Sentence tokenization
- **scikit-learn**: Evaluation metrics

## Fine-Tuning Benefits

The fine-tuned model with focal loss:
- Learns your specific domain and terminology
- Reduces false positives (conservative predictions)
- Improves precision and recall on your data
- Faster inference than zero-shot classification

