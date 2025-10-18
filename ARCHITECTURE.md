# System Architecture

## Overview

The Ensemble Labeling System is a multi-stage pipeline for classifying therapy-related text with human-in-the-loop validation and gradual automation.

## Component Structure

```
app/
├── config.py                    - Central configuration
├── pipeline/
│   ├── chunker.py              - Sentence segmentation (existing)
│   ├── classifier.py           - Single model classifier (existing)
│   ├── aggregator.py           - Results aggregation (existing)
│   ├── synthetic_generator.py - LLM-based data generation (NEW)
│   ├── ensemble_classifier.py - Multi-model voting system (NEW)
│   ├── accuracy_tracker.py    - Per-category metrics (NEW)
│   └── labeling_system.py     - Human review interface (NEW)
└── storage/
    ├── database.py             - SQLite operations (NEW)
    └── schemas.py              - Data models (NEW)
```

## Data Flow

### 1. Synthetic Data Generation
```
Nebius API (GPT-4) → Category Prompts → Generated Sentences → Database
```

### 2. Ensemble Classification
```
Input Text → Chunker → 5 Models → Voting → Entropy Check → Database
```

### 3. Human Review
```
Database → Labeling System → CLI Interface → Human Decision → Updated Sample
```

### 4. Metrics Tracking
```
Labeled Samples → Accuracy Tracker → Per-Category Metrics → Database
```

### 5. Auto-Accept Decision
```
Metrics + Entropy + Agreement → Should Review? → Auto-Accept or Human Review
```

## Key Classes

### EnsembleClassifier
- Loads multiple zero-shot classification models
- Runs parallel predictions on input text
- Implements supermajority voting (4/5 models must agree)
- Calculates prediction entropy
- Flags high-uncertainty cases for human review

### AccuracyTracker
- Monitors per-category performance metrics
- Calculates precision, recall, F1, accuracy
- Determines when categories are ready for auto-accept
- Requires >= 50 samples and >= 90% accuracy

### LabelingSystem
- Rich CLI interface for human review
- Shows sentence, predictions, entropy, agreement
- Allows accept/change/skip actions
- Tracks labeling session statistics

### LabelingDatabase
- SQLite storage for all labeled samples
- Tracks model predictions vs human labels
- Stores per-category metrics over time
- Exports training data for fine-tuning

### SyntheticDataGenerator
- Uses Nebius API (OpenAI-compatible)
- Category-specific prompts for each therapy attribute
- Generates diverse, realistic medical text
- Creates balanced training datasets

## Decision Logic

### Needs Review?
A sample needs human review if:
1. Agreement score < 0.8 (supermajority threshold)
2. Entropy > 1.5 (high uncertainty)
3. Category has human_review_enabled = True
4. Category hasn't reached auto-accept criteria

### Can Auto-Accept?
A category can auto-accept if:
1. >= 50 labeled samples (min_samples_for_handoff)
2. >= 90% accuracy (category_accuracy_threshold)
3. human_review_enabled = False for that category

### Vote Calculation
```python
votes = [model1_pred, model2_pred, ...]
most_common = Counter(votes).most_common(1)
winning_label = most_common[0]
agreement_score = count / total_models
```

### Entropy Calculation
```python
probabilities = [count/total for count in vote_counts]
entropy = scipy.stats.entropy(probabilities, base=2)
```

## Database Schema

### labeled_samples
- id: PRIMARY KEY
- sentence: TEXT
- human_label: TEXT
- model_predictions: JSON
- ensemble_prediction: TEXT
- confidence: REAL
- entropy: REAL
- agreement_score: REAL
- needs_review: BOOLEAN
- timestamp: TEXT
- source: TEXT (synthetic/real)

### category_metrics
- category: PRIMARY KEY
- total_samples: INTEGER
- correct_predictions: INTEGER
- precision, recall, f1_score, accuracy: REAL
- can_auto_accept: BOOLEAN
- last_updated: TEXT

## Configuration Parameters

### Ensemble Settings
- `ensemble_models`: List of 5 HuggingFace model IDs
- `supermajority_threshold`: 0.8 (80% agreement)
- `entropy_threshold`: 1.5 (max acceptable uncertainty)

### Handoff Settings
- `category_accuracy_threshold`: 0.90 (90% accuracy)
- `min_samples_for_handoff`: 50 samples
- `human_review_enabled`: Per-category flags

### API Settings
- `nebius_api_key`: From environment variable
- `nebius_base_url`: API endpoint
- `nebius_model`: Model name (gpt-4)

## Modes of Operation

### Mode 1: Bootstrap (generate → label)
```bash
python main.py generate --samples 10 --label
python main.py label --batch-size 20
```

### Mode 2: Production (classify with auto-accept)
```bash
python main.py classify --ensemble --auto-accept --file input.txt
```

### Mode 3: Monitoring (stats and reports)
```bash
python main.py stats
python main.py stats --category efficacy_rate
```

### Mode 4: Training Prep (export for fine-tuning)
```bash
python main.py export --output training.jsonl
```

## Gradual Handoff Strategy

```
Phase 1: Bootstrap (Week 1-2)
- Generate 100-200 synthetic samples per category
- 100% human review
- Build initial labeled dataset

Phase 2: Active Learning (Week 3-4)
- Classify real data with ensemble
- Route high-entropy to human
- Track per-category accuracy

Phase 3: Selective Automation (Week 5+)
- Enable auto-accept for high-accuracy categories
- Continue human review for others
- Monitor for accuracy drift

Phase 4: Fine-tuning (Future)
- Export labeled data
- Train category-specific models
- Replace zero-shot ensemble with fine-tuned models
```

## Performance Considerations

### Ensemble Inference
- 5 models running in parallel
- ~5-10s per sentence on CPU
- ~1-2s per sentence on GPU
- Consider batching for efficiency

### Database Performance
- SQLite handles 10K+ samples easily
- Indexed on human_label and needs_review
- Export to JSONL for training

### API Costs
- Synthetic generation uses Nebius API
- ~10 samples per request
- Monitor token usage and costs

## Future Enhancements

1. Fine-tuned model ensemble
2. Active learning sample selection
3. Confidence calibration
4. Multi-label classification
5. Streaming inference
6. Web UI for labeling
7. Inter-annotator agreement tracking
8. Model performance comparison

