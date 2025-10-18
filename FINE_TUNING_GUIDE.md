# Fine-Tuning Guide

This guide explains how to use the human-in-the-loop labeling system and fine-tune your therapy classification model.

## Overview

The system uses focal loss (α=0.75, γ=2.0) to penalize false positives more heavily than false negatives. This makes the model more conservative about classifying text into categories.

## Workflow

### 1. Collect & Label Samples

**Extract samples from a text file:**
```bash
python label.py path/to/your/text_file.txt
```

This will:
1. Extract sentences from the text file
2. Store them in the SQLite database
3. Start an interactive labeling session

**Label existing samples:**
```bash
python label.py
```

**CLI Labeling Controls:**
- `y` = Yes (positive label for this category)
- `n` = No (negative label for this category)
- `s` = Skip this sample
- `u` = Undo last sample's labels
- `q` = Quit and save progress

**Tips:**
- The model's predictions are shown to help guide you
- All 13 categories will be presented for each sample
- Labels are saved immediately after each sample
- You can quit anytime and resume later

### 2. Check Progress

During labeling, statistics are shown at the end of each session:
- Total labeled samples
- Positive/negative/total labels per category

**Recommended minimum before training:**
- 50-100 samples per category (minimum viable)
- 200-500 samples per category (good performance)
- 500-1000+ samples per category (production-ready)

With multi-label overlap, aim for ~500-1000 total samples to start.

### 3. Train the Model

```bash
python train.py
```

**Training options:**
```bash
python train.py --epochs 15 --batch-size 16 --learning-rate 3e-5
```

**What happens during training:**
1. Data is split 80/20 train/validation
2. BART-large-mnli is fine-tuned with a classification head
3. Focal loss penalizes false positives (α=0.75)
4. Early stopping prevents overfitting (patience=3)
5. Best model is saved to `models/finetuned/model_TIMESTAMP/`

**Training outputs:**
- Per-epoch metrics (loss, F1, precision, recall)
- Per-category performance metrics
- Model checkpoint saved to disk

### 4. Use the Fine-Tuned Model

After training completes, update `app/config.py`:

```python
finetuned_model_path = "models/finetuned/model_20250118_143022"
```

Now run your main pipeline:
```bash
python main.py
```

The classifier will automatically use the fine-tuned model instead of zero-shot classification.

## Configuration

### Focal Loss Parameters (`app/config.py`)

```python
focal_loss_alpha = 0.75
focal_loss_gamma = 2.0
```

- **alpha (0.75)**: Weights the loss for positive vs negative classes
  - Higher alpha = more penalty for false positives
  - Lower alpha = more penalty for false negatives

- **gamma (2.0)**: Focuses on hard examples
  - Higher gamma = focus more on misclassified examples
  - Lower gamma = treat all examples more equally

### Class Weights

```python
focal_loss_class_weights = [1.0] * 13
```

Adjust individual category weights if some categories are more important:
```python
focal_loss_class_weights = [
    1.5,  # efficacy_extent - more important
    1.5,  # efficacy_rate
    1.2,  # side_effect_severity
    1.2,  # side_effect_risk
    1.0,  # cost
    1.0,  # effect_size_evidence
    0.8,  # trial_design - less critical
    0.8,  # trial_length
    1.0,  # num_participants
    1.0,  # sex_participants
    1.0,  # age_range_participants
    0.8,  # other_participant_info
    0.8,  # other_study_info
]
```

### Training Hyperparameters

```python
training_batch_size = 8
training_epochs = 10
training_learning_rate = 2e-5
training_warmup_steps = 100
training_patience = 3
training_dropout = 0.1
```

## Database

Data is stored in SQLite (`therapy_labels.db` by default).

**Tables:**
- `samples`: Text samples with labeling status
- `labels`: Multi-label annotations per sample
- `training_runs`: Training history and metrics

**Custom database path:**
```bash
python label.py --db custom_path.db
python train.py --db custom_path.db
```

## Advanced Usage

### Batch Collection Without Labeling

```bash
python label.py file1.txt --collect-only
python label.py file2.txt --collect-only
python label.py file3.txt --collect-only
python label.py
```

### Force Training With Insufficient Data

```bash
python train.py --force
```

### Adjust Confidence Threshold

After fine-tuning, you may want to adjust the confidence threshold in `app/config.py`:

```python
confidence_threshold = 0.3
```

Lower threshold = more predictions (higher recall, lower precision)
Higher threshold = fewer predictions (lower recall, higher precision)

## Troubleshooting

**"No unlabeled samples found"**
- Run `python label.py <text_file>` to collect samples first

**Training fails with "No training data available"**
- Label more samples using `python label.py`

**Model predictions are all low confidence**
- You may need more training data
- Try lowering `confidence_threshold` in config
- Check if categories match your actual data

**Out of memory during training**
- Reduce `training_batch_size` (try 4 or 2)
- Use CPU instead: Set `device = "cpu"` in config

## Iterative Improvement

1. Start with ~500 labeled samples
2. Train initial model
3. Evaluate per-category metrics
4. Focus labeling on weak categories
5. Re-train with more data
6. Repeat until satisfactory performance

The focal loss will help prevent overfitting to majority classes and penalize false positives as desired.

