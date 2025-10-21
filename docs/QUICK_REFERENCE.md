# Quick Reference Card

## Commands

### Labeling
```bash
python label.py sample_data.txt
python label.py
python label.py --batch-size 100
```

### Training
```bash
python train.py
python train.py --epochs 15 --batch-size 16
python train.py --force
```

### Running Pipeline
```bash
python main.py
```

## Labeling Controls

| Key | Action |
|-----|--------|
| `y` | Yes (positive label) |
| `n` | No (negative label) |
| `s` | Skip this sample |
| `u` | Undo last sample |
| `q` | Quit and save |

## Key Configuration Settings

### app/config.py

```python
finetuned_model_path = "models/finetuned/model_TIMESTAMP"
confidence_threshold = 0.2
focal_loss_alpha = 0.75
focal_loss_gamma = 2.0
```

### Alpha Parameter Guide
- **0.5**: Balanced (equal weight to FP and FN)
- **0.75**: Default (penalizes false positives more)
- **0.9**: Very conservative (strongly avoid false positives)

### Confidence Threshold Guide
- **0.1-0.2**: High recall, lower precision
- **0.3-0.4**: Balanced
- **0.5+**: High precision, lower recall

## Recommended Dataset Sizes

| Category | Samples Needed | Total Dataset |
|----------|----------------|---------------|
| Minimum viable | 50-100 each | 500-1000 |
| Good performance | 200-500 each | 1500-3000 |
| Production-ready | 500-1000+ each | 3000-5000+ |

## Common Issues

### "No unlabeled samples"
→ Run: `python label.py sample_data.txt`

### "No training data"
→ Label more samples first

### Out of memory
→ Reduce batch size: `python train.py --batch-size 4`

### Model not loading
→ Check path in `app/config.py`

## File Structure

```
hackaging-processor/
├── label.py                    # Label samples
├── train.py                    # Train model
├── main.py                     # Run pipeline
├── therapy_labels.db           # SQLite database
├── app/
│   ├── config.py              # Configuration
│   ├── database/
│   │   ├── db.py              # Database manager
│   │   └── schema.py          # Tables
│   ├── labeling/
│   │   ├── cli_labeler.py     # Interactive UI
│   │   └── sample_collector.py
│   ├── training/
│   │   ├── focal_loss.py      # Loss function
│   │   ├── dataset.py         # Data loader
│   │   └── trainer.py         # Training loop
│   └── pipeline/
│       ├── classifier.py      # Model wrapper
│       ├── chunker.py         # Text splitting
│       └── aggregator.py      # Results
└── models/
    └── finetuned/             # Saved models
```

## Workflow Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Collect samples: `python label.py your_text.txt`
- [ ] Label 500-1000 samples
- [ ] Check statistics (shown after labeling)
- [ ] Train model: `python train.py`
- [ ] Note the model path from training output
- [ ] Update `app/config.py` with model path
- [ ] Test pipeline: `python main.py`
- [ ] Iterate: label more, retrain if needed

## Evaluation Metrics

After training, check these per category:
- **Precision**: How many predictions were correct?
- **Recall**: How many actual positives were found?
- **F1-Score**: Harmonic mean of precision and recall

For false positive avoidance, focus on **precision**.

## Getting Help

- Full guide: `FINE_TUNING_GUIDE.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- Main README: `README.md`

