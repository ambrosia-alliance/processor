# Manual Labeling Workflow

## Overview

Generate realistic synthetic therapy text samples WITHOUT labels, then manually label them using the interactive CLI labeler.

## Two-Step Process

### Step 1: Generate Unlabeled Text Samples

```bash
python generate_unlabeled.py --samples 50
```

This creates 50 realistic therapy-related text samples and inserts them as **unlabeled** into the database.

**Options:**
- `--samples N`: Number of samples to generate (default: 50)
- `--dry-run`: Preview samples without inserting into database
- `--db PATH`: Database path (default: therapy_labels.db)

**Preview first:**
```bash
python generate_unlabeled.py --samples 50 --dry-run
```

### Step 2: Label the Samples Manually

```bash
python label.py --batch-size 20
```

This opens the interactive CLI labeler where you can:
- View each sample
- Mark categories as present/absent
- Skip samples
- Track progress

**Labeling Commands:**
- Enter category numbers (space-separated) to mark as present
- `s` - Skip current sample
- `q` - Quit session
- Progress is saved after each sample

## Complete Workflow Example

```bash
export NEBIUS_API_KEY="your-key-here"

python generate_unlabeled.py --samples 100

python label.py --batch-size 25

python train.py --batch-size 2

python main.py
```

## Why This Workflow?

**Benefits:**
1. **Human validation** - You control the ground truth
2. **Realistic text** - AI generates diverse, natural examples
3. **Efficient** - Faster than writing samples manually
4. **Quality control** - Review each sample before labeling

**Use cases:**
- Creating gold-standard training data
- Validating synthetic labeled data
- Testing edge cases
- Building domain-specific datasets

## Comparison: Two Generation Methods

### `generate_synthetic.py` (Auto-labeled)
- Generates text + labels automatically
- Fast, no manual work
- Good for bulk training data
- Labels may have some errors

### `generate_unlabeled.py` (Manual labeling)
- Generates text only
- Requires manual labeling
- Higher quality labels
- Good for validation/test sets

## Tips

1. Start with a small batch (20-50 samples) to test
2. Use `--dry-run` to preview quality before inserting
3. Label in focused sessions (20-30 samples at a time)
4. Mix auto-labeled and manually-labeled data for best results
5. Review auto-labeled samples periodically for quality

## Database Stats

Check your data:
```bash
sqlite3 therapy_labels.db "SELECT labeled, COUNT(*) FROM samples GROUP BY labeled;"
```

Output:
```
0|150    # Unlabeled samples
1|130    # Labeled samples
```

