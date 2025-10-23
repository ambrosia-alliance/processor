# Getting Started with Fine-Tuning

## Installation

Make sure you have all dependencies:

```bash
pip install -r requirements.txt
```

The new dependency added is `scikit-learn` for evaluation metrics.

## Quick Start (3 Steps)

### Step 1: Label Your First Batch

```bash
python label.py sample_data.txt
```

This will:
1. Extract 30 sentences from the sample file
2. Save them to the database
3. Start an interactive labeling session

**Labeling tips:**
- Use `y` for positive, `n` for negative
- The model shows predictions to guide you
- Press `s` to skip difficult samples
- Press `q` anytime to save and quit

**Goal:** Label at least 500-1000 samples before training

### Step 2: Train Your Model

```bash
python train.py
```

This will:
1. Check if you have enough labeled data
2. Split data 80/20 train/validation
3. Fine-tune BART with focal loss (α=0.75, γ=2.0)
4. Save the best model

**Training time:** ~10-30 minutes depending on data size and GPU availability

### Step 3: Use Your Fine-Tuned Model

Edit `app/config.py`:

```python
finetuned_model_path = "models/finetuned/model_20250118_143022"
```

Then run the pipeline:

```bash
python main.py
```

## Understanding Focal Loss (α=0.75)

The alpha parameter controls the false positive vs false negative trade-off:

```
α = 0.5  → Equal weight
α = 0.75 → Penalize false positives more (DEFAULT)
α = 0.9  → Strongly avoid false positives
```

**Why 0.75?** This means false positives are penalized 3x more than false negatives, matching your requirement that "false positives are worse than false negatives."

## Labeling Workflow Example

```bash
python label.py data/study1.txt
python label.py data/study2.txt
python label.py data/study3.txt
python label.py
python label.py
python label.py
```

After each session, you'll see statistics like:

```
Total labeled samples: 523

Labels per category:
Category                       Positive   Negative   Total
------------------------------------------------------------
efficacy_extent                45         478        523
efficacy_rate                  67         456        523
side_effect_severity           34         489        523
...
```

## How Much Data Do I Need?

| Stage | Samples | What You Get |
|-------|---------|--------------|
| Proof of concept | 100-200 | See if it works |
| Initial model | 500-1000 | Baseline performance |
| Production | 1500-3000+ | Reliable predictions |

Start with 500-1000 and iterate based on results.

## Monitoring Training

During training, watch for:

```
Epoch 1/10
  Train Loss: 0.4521
  Val Loss: 0.3892
  Val F1 (macro): 0.6234
  Val Precision (macro): 0.7123
  Val Recall (macro): 0.5567
  Saved best model to models/finetuned/model_20250118_143022
```

**Good signs:**
- Validation loss decreasing
- Precision > 0.7 (indicates low false positives)
- F1 score increasing

**Bad signs:**
- Train loss << Val loss (overfitting - need more data)
- Precision < 0.5 (too many false positives)
- No improvement after 3 epochs (early stopping)

## Adjusting for Fewer False Positives

If you're still getting too many false positives:

1. **Increase alpha** in `app/config.py`:
```python
focal_loss_alpha = 0.85
```

2. **Increase confidence threshold**:
```python
confidence_threshold = 0.3
```

3. **Add category-specific weights**:
```python
focal_loss_class_weights = [
    1.5,  # efficacy_extent - critical
    1.5,  # efficacy_rate - critical
    1.2,  # side_effect_severity
    1.2,  # side_effect_risk
    1.0,  # cost
    1.0,  # effect_size_evidence
    0.8,  # trial_design
    0.8,  # trial_length
    1.0,  # num_participants
    1.0,  # sex_participants
    1.0,  # age_range_participants
    0.8,  # other_participant_info
    0.8,  # other_study_info
]
```

Then retrain with `python train.py`

## Troubleshooting

### "No unlabeled samples found"
→ You've labeled everything! Add more text files:
```bash
python label.py new_data.txt
```

### "Data requirements not met"
→ You need more labels. The system recommends at least 50 per category. Continue labeling or use `--force`:
```bash
python train.py --force
```

### "Out of memory during training"
→ Reduce batch size:
```bash
python train.py --batch-size 4
```

### Model loads but predictions are wrong
→ You may need more training data or to adjust hyperparameters

## Iterative Improvement Loop

```
┌─────────────────┐
│  Label samples  │
│    (500-1000)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Train model    │
│  (10-30 min)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Evaluate metrics│
│ Check precision │
└────────┬────────┘
         │
         ▼
    ┌───────┐
    │ Good? │───Yes──► Deploy to production
    └───┬───┘
        │
       No
        │
        ▼
┌─────────────────┐
│ Focus on weak   │
│ categories      │
│ Label more data │
└────────┬────────┘
         │
         └──────► Back to training
```

## Files Created

After your first labeling session:
- `therapy_labels.db` - SQLite database with all labels

After training:
- `models/finetuned/model_TIMESTAMP/` - Your trained model
  - `model.pt` - Model weights
  - `config.json` - Model configuration
  - `tokenizer files` - For text processing

## Next Steps

1. **Start labeling now:** `python label.py sample_data.txt`
2. **Label in multiple sessions** until you reach 500-1000 samples
3. **Train your first model:** `python train.py`
4. **Evaluate the results** and iterate

Good luck! 🚀

For detailed information, see:
- `FINE_TUNING_GUIDE.md` - Comprehensive guide
- `QUICK_REFERENCE.md` - Command cheat sheet
- `IMPLEMENTATION_SUMMARY.md` - Technical details

