# Multi-Label Classification Updates

## Summary

The system has been updated to support multi-label classification where one sentence can be classified into multiple categories simultaneously.

## What Changed

### 1. Ensemble Classifier ✓
**File:** `app/pipeline/ensemble_classifier.py`

**Changes:**
- Added `label_threshold` parameter (default: 0.5)
- Changed `multi_label=True` in pipeline calls
- Updated methods to handle lists of labels instead of single labels:
  - `classify_sentence()` now returns `ensemble_predictions` (list)
  - `_vote_multilabel()` aggregates votes across multiple labels
  - `_calculate_entropy_multilabel()` handles multi-label entropy
  - `_needs_review_multilabel()` checks minimum agreement across labels
- Added comprehensive docstrings to all methods

**Example:**
```python
result = ensemble.classify_sentence("TPE costs $3000 and has 75% efficacy.")
# Returns:
{
    "ensemble_predictions": ["cost", "efficacy_rate"],
    "agreement_scores": {"cost": 1.0, "efficacy_rate": 0.8},
    ...
}
```

### 2. Storage Schemas ✓
**File:** `app/storage/schemas.py`

**Changes:**
- `LabeledSample.human_labels` changed from `str` to `List[str]`
- `LabeledSample.ensemble_predictions` changed from `str` to `List[str]`
- `LabeledSample.model_predictions` changed to `Dict[str, List[str]]`
- `LabeledSample.agreement_scores` changed to `Dict[str, float]`
- Added module and class docstrings

### 3. Configuration ✓
**File:** `app/config.py`

**Changes:**
- Added `label_threshold: float = 0.5` parameter
- This controls minimum score for a label to be accepted

### 4. Synthetic Generator ✓
**File:** `app/pipeline/synthetic_generator.py`

**Changes:**
- Added module docstring
- Added class docstring
- Added method docstrings for all public methods

## What Still Needs Update

### 1. Database Layer
**File:** `app/storage/database.py`

**Needs:**
- Update schema to store lists instead of single strings
- Change `human_label` column to support JSON arrays
- Change `ensemble_prediction` column to support JSON arrays
- Update `_row_to_sample()` to parse JSON arrays
- Update queries to handle multi-label searches

### 2. Accuracy Tracker
**File:** `app/pipeline/accuracy_tracker.py`

**Needs:**
- Handle multi-label metrics calculation
- Update precision/recall/F1 for multi-label scenarios
- Use `multilabel_confusion_matrix` from sklearn
- Add docstrings

### 3. Labeling System
**File:** `app/pipeline/labeling_system.py`

**Needs:**
- Update CLI to allow selecting multiple categories
- Display multiple labels in review interface
- Allow adding/removing labels interactively
- Add docstrings

### 4. Main Pipeline
**File:** `main.py`

**Needs:**
- Update `EnsemblePipeline` to handle multi-label results
- Fix references from `ensemble_prediction` to `ensemble_predictions`
- Fix references from `human_label` to `human_labels`
- Update display logic for multiple labels
- Add docstrings to mode functions

## Testing Multi-Label

### Quick Test
```python
from app.pipeline.ensemble_classifier import EnsembleClassifier

ensemble = EnsembleClassifier(label_threshold=0.5)

test_sentence = "TPE achieved 75% efficacy in trials with costs of $3000 per session."

result = ensemble.classify_sentence(test_sentence)

print(f"Sentence: {result['sentence']}")
print(f"Predictions: {result['ensemble_predictions']}")
print(f"Agreement: {result['agreement_scores']}")
print(f"Needs review: {result['needs_review']}")
```

### Expected Output
```
Sentence: TPE achieved 75% efficacy in trials with costs of $3000 per session.
Predictions: ['efficacy_rate', 'cost']
Agreement: {'efficacy_rate': 0.8, 'cost': 1.0}
Needs review: False
```

## Configuration Options

**Label Threshold (`label_threshold`):**
- Default: 0.5
- Controls minimum confidence score for a label to be accepted
- Higher values = fewer labels per sentence
- Lower values = more labels per sentence

**Supermajority Threshold (`supermajority_threshold`):**
- Default: 0.8 (4/5 models)
- Applied per label independently
- A label needs 80% model agreement to be accepted

## Migration Notes

### For Existing Databases
If you have existing data in the database:

1. Backup current database
2. Run migration script to convert single labels to arrays
3. Update all references in code

### For New Installations
No migration needed - just use the new schema.

## Benefits of Multi-Label

1. **More Information:** Sentences containing multiple types of information are properly classified
2. **Better Training Data:** Fine-tuned models get richer supervision signal
3. **Realistic:** Medical papers often discuss multiple aspects in one sentence
4. **Flexible:** System can handle both single and multiple labels

## Next Steps

1. Complete database updates for multi-label storage
2. Update accuracy tracker for multi-label metrics
3. Update labeling system CLI for multi-label selection
4. Test end-to-end workflow
5. Update documentation with multi-label examples

