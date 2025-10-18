# Therapy Classification Pipeline

A Python ML pipeline that processes medical therapy text through ensemble classification with human-in-the-loop labeling and gradual automation.

## Features

- Sentence-level text chunking
- Ensemble classification with 5 zero-shot models
- Synthetic data generation via Nebius API
- Human-in-the-loop labeling with CLI interface
- Per-category accuracy tracking
- Gradual automation handoff (90% accuracy threshold)
- Supermajority voting with entropy-based review
- SQLite storage for labeled data
- Training data export for fine-tuning

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
export NEBIUS_API_KEY="your-api-key-here"
```

## Quick Start

### 1. Generate synthetic training data
```bash
python main.py generate --samples 10 --label
```

### 2. Label samples with human review
```bash
python main.py label --batch-size 20
```

### 3. View accuracy metrics
```bash
python main.py stats
```

### 4. Enable auto-accept for ready categories
```bash
python main.py auto-accept
```

### 5. Classify with ensemble
```bash
python main.py classify --ensemble --auto-accept --file input.txt
```

## Usage Modes

### Generate Synthetic Data
```bash
python main.py generate --samples 15 --categories efficacy_rate,cost --output data.json
```

### Human Labeling Session
```bash
python main.py label --batch-size 30
```

### Ensemble Classification
```bash
python main.py classify --ensemble --text "TPE achieved 75% efficacy in trials."
```

### View Statistics
```bash
python main.py stats --category efficacy_rate
```

### Export Training Data
```bash
python main.py export --output training_data.jsonl
```

## Legacy Single-Model Usage

```python
from main import TherapyClassificationPipeline

pipeline = TherapyClassificationPipeline()
results = pipeline.process("Your therapy text here...")
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

**Ensemble Settings:**
- `ensemble_models`: List of 5 zero-shot models
- `supermajority_threshold`: Agreement threshold (default: 0.8)
- `entropy_threshold`: Max entropy for auto-accept (default: 1.5)

**Handoff Settings:**
- `category_accuracy_threshold`: Required accuracy (default: 0.90)
- `min_samples_for_handoff`: Minimum samples (default: 50)
- `human_review_enabled`: Per-category flags

**API Settings:**
- `nebius_api_key`: Nebius API key (from env)
- `nebius_model`: Model for synthetic generation (default: gpt-4)

## Architecture

**Ensemble Classification:**
- 5 zero-shot models voting in parallel
- Supermajority threshold (4/5 agreement)
- Entropy-based uncertainty detection

**Human-in-the-Loop:**
- Rich CLI for labeling sessions
- Per-category accuracy tracking
- Gradual automation handoff

**Storage:**
- SQLite database for labeled samples
- Per-category metrics history
- Training data export

**Models:**
- BART-MNLI, DeBERTa, RoBERTa, DistilBERT, NLI-DeBERTa

See `ARCHITECTURE.md` for detailed system design.
See `USAGE.md` for complete usage guide.

