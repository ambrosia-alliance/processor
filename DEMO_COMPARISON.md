# Model Comparison Demo

## Overview

The updated `main.py` now demonstrates the contrast between the original zero-shot BART model and your finetuned model.

## Usage

```bash
python main.py
```

## What It Does

1. **Runs Original Model** - Zero-shot BART-large-MNLI classifier
2. **Finds Latest Finetuned Model** - Automatically searches `models/finetuned/` for the most recent trained model
3. **Runs Finetuned Model** - Uses your custom-trained model if available
4. **Shows Comparison** - Side-by-side results with confidence changes

## Example Output

```
===============================================================================
THERAPY CLASSIFICATION DEMO - MODEL COMPARISON
===============================================================================

Base Model: facebook/bart-large-mnli
Device: cuda

Running ORIGINAL MODEL (Zero-Shot)...

===============================================================================
ORIGINAL MODEL RESULTS
===============================================================================

EFFICACY_RATE
  Count: 1
  Avg Confidence: 85.23%
  Sentences:
    - Therapeutic Plasma Exchange (TPE) has demonstrated a 75% efficacy rate in...
      (confidence: 85.23%)

...

Found finetuned model: models/finetuned/model_20251018_143022

Running FINETUNED MODEL...

===============================================================================
FINETUNED MODEL RESULTS
===============================================================================

EFFICACY_RATE
  Count: 1
  Avg Confidence: 92.45%
  Sentences:
    - Therapeutic Plasma Exchange (TPE) has demonstrated a 75% efficacy rate in...
      (confidence: 92.45%)

...

===============================================================================
COMPARISON SUMMARY
===============================================================================

efficacy_rate:
  Original Model: 1 detections
  Finetuned Model: 1 detections
  Confidence Change: 85.23% → 92.45%

trial_design:
  Original Model: 1 detections
  Finetuned Model: 2 detections
  Confidence Change: 78.12% → 88.67%
```

## Notes

- If no finetuned model exists, only original model results are shown
- The script automatically finds the most recently trained model
- Both models process the same sample text for fair comparison

## Training Workflow

1. Generate synthetic data: `python generate_synthetic.py`
2. Train model: `python train.py --batch-size 2`
3. Compare results: `python main.py`

## CUDA Memory Fix

The default batch size has been reduced from 8 to 2 in `app/config.py` to prevent CUDA out of memory errors on 11GB GPUs.

To override:
```bash
python train.py --batch-size 4
```

