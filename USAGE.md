# Ensemble Labeling System - Usage Guide

This system implements an ensemble classification pipeline with synthetic data generation, human-in-the-loop labeling, and gradual automation handoff.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variable for Nebius API:
```bash
export NEBIUS_API_KEY="your-api-key-here"
```

## Workflow

### Phase 1: Bootstrap with Synthetic Data

Generate synthetic training data using Nebius LLM:

```bash
python main.py generate --samples 10 --label
```

This generates 10 samples per category and adds them to the database for review.

### Phase 2: Human Labeling

Start a labeling session to review and label samples:

```bash
python main.py label --batch-size 20
```

Interactive CLI allows you to:
- Accept ensemble predictions
- Override with correct labels
- Skip uncertain samples
- Track progress

### Phase 3: Monitor Metrics

View per-category accuracy and readiness:

```bash
python main.py stats
```

Detailed report for a specific category:

```bash
python main.py stats --category efficacy_rate
```

### Phase 4: Enable Auto-Accept

Check which categories are ready for automation:

```bash
python main.py auto-accept
```

System will prompt you to enable auto-accept for categories with:
- >= 50 labeled samples (configurable)
- >= 90% accuracy (configurable)

### Phase 5: Production Classification

Classify new text with ensemble:

```bash
python main.py classify --ensemble --text "Your text here"
```

With auto-accept enabled for ready categories:

```bash
python main.py classify --ensemble --auto-accept --file input.txt
```

### Phase 6: Export Training Data

Export labeled data for fine-tuning:

```bash
python main.py export --output data/training.jsonl
```

## Command Reference

### Generate Synthetic Data

```bash
python main.py generate [options]
  --samples N          Samples per category (default: 10)
  --categories LIST    Comma-separated categories
  --output FILE        Save to JSON file
  --label              Add to database for labeling
```

### Label Samples

```bash
python main.py label [options]
  --batch-size N       Samples per session (default: 10)
```

### Classify Text

```bash
python main.py classify [options]
  --text TEXT          Text to classify
  --file FILE          File to classify
  --ensemble           Use ensemble classifier
  --auto-accept        Auto-accept low-entropy predictions
```

### View Statistics

```bash
python main.py stats [options]
  --category NAME      Detailed report for category
```

### Export Data

```bash
python main.py export [options]
  --output FILE        Output file path
```

### Auto-Accept Management

```bash
python main.py auto-accept
```

## Configuration

Edit `app/config.py` to customize:

- `ensemble_models`: List of models in ensemble
- `supermajority_threshold`: Required agreement (default: 0.8 = 4/5 models)
- `entropy_threshold`: Maximum entropy for auto-accept (default: 1.5)
- `category_accuracy_threshold`: Required accuracy for handoff (default: 0.90)
- `min_samples_for_handoff`: Minimum labeled samples (default: 50)
- `human_review_enabled`: Per-category review flags

## Database

SQLite database stored at `data/labeling.db` contains:
- Labeled samples with predictions and metadata
- Per-category accuracy metrics
- Training history

## Categories

The system classifies into these therapy-related categories:
1. efficacy_extent
2. efficacy_rate
3. side_effect_severity
4. side_effect_risk
5. cost
6. effect_size_evidence
7. trial_design
8. trial_length
9. num_participants
10. sex_participants
11. age_range_participants
12. other_participant_info
13. other_study_info

## Ensemble Models

Default ensemble uses these zero-shot classifiers:
- facebook/bart-large-mnli
- microsoft/deberta-v3-base
- roberta-large-mnli
- typeform/distilbert-base-uncased-mnli
- cross-encoder/nli-deberta-v3-base

## Metrics Tracking

For each category, the system tracks:
- Total labeled samples
- Accuracy, Precision, Recall, F1
- Auto-accept eligibility
- Last update timestamp

## Gradual Handoff

The system gradually reduces human review per category:
1. Start: 100% human review for all categories
2. Label >= 50 samples per category
3. Achieve >= 90% accuracy consistently
4. Enable auto-accept for that category
5. High-entropy cases still go to human review
6. Other categories remain in human review

## Example Workflow

```bash
export NEBIUS_API_KEY="your-key"

python main.py generate --samples 15 --label

python main.py label --batch-size 30

python main.py stats

python main.py auto-accept

python main.py classify --ensemble --auto-accept --file research_paper.txt

python main.py stats --category efficacy_rate

python main.py export --output final_training_data.jsonl
```

