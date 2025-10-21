# Synthetic Data Generator Guide

## Overview

The `generate_synthetic.py` script uses Nebius AI (DeepSeek-V3) to generate realistic labeled therapy classification data focused on Therapeutic Plasma Exchange (TPE) and longevity research for training and testing.

## Setup

1. Set your Nebius API key as an environment variable:
```bash
export NEBIUS_API_KEY="your-api-key-here"
```

2. Ensure the virtual environment is activated:
```bash
source hackaging/bin/activate
```

## Usage

### Basic Usage (Default: 390 samples, 30% multi-category)
```bash
python generate_synthetic.py
```

### Dry Run (Preview without inserting)
```bash
python generate_synthetic.py --dry-run
```

### Custom Configuration
```bash
python generate_synthetic.py --samples 200 --multi-ratio 0.4
```

### Options
- `--db PATH`: Database path (default: therapy_labels.db)
- `--samples N`: Total number of samples to generate (default: 390)
- `--multi-ratio F`: Ratio of multi-category samples, 0.0-1.0 (default: 0.3)
- `--dry-run`: Preview generation without inserting to database

## What It Does

1. **Generates Single-Category Samples**: Creates ~21 samples per category (13 categories total = 273 samples)
2. **Generates Multi-Category Samples**: Creates ~117 samples with 2-3 relevant categories
3. **Inserts to Database**: Adds samples with labels and marks them as labeled
4. **Source Tag**: All synthetic samples are tagged with source "synthetic_tpe_longevity_v1"
5. **Focus**: All samples are focused on Therapeutic Plasma Exchange (TPE) and longevity research

## Categories Covered

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

## Verification

After generation, verify the data was inserted:

### Using sqlite3 CLI
```bash
sqlite3 therapy_labels.db

SELECT COUNT(*) FROM samples WHERE source = 'synthetic_tpe_longevity_v1';
SELECT category, COUNT(*) FROM labels GROUP BY category;
.quit
```

### Using Python
```python
from app.database.db import DatabaseManager

with DatabaseManager('therapy_labels.db') as db:
    stats = db.get_label_statistics()
    for category, counts in stats.items():
        print(f"{category}: {counts['total']} total ({counts['positive']} positive)")
```

## Focus Areas

The generator creates sentences focused on:

### TPE Benefits for Longevity:
- Biological age reduction (1.32-2.61 year reductions documented)
- Heavy metal and toxin detoxification (25-100% reductions)
- Immune system rebalancing
- Improved cognitive function
- Blood flow improvements

### TPE Side Effects:
- Low blood pressure and dizziness
- Infection risk from IV lines
- Blood clotting and bleeding complications
- Allergic reactions to replacement fluids

## Example Output

```
Generation Plan:
  Total samples: 390
  Single-category: 273 (21 per category)
  Multi-category: 117
  Dry run: False

Generating single-category samples...
  [1/13] Generating 21 samples for 'efficacy_extent'...
    Generated 21 samples
  [2/13] Generating 21 samples for 'efficacy_rate'...
    Generated 21 samples
  ...

Generating multi-category samples...
  [1/24] Generating 5 multi-category samples...
    Generated 5 samples
  ...

Generated 390 total samples

Inserting into database...
Inserted 390 samples

Category distribution:
  efficacy_extent: 35
  efficacy_rate: 42
  side_effect_severity: 38
  ...

Multi-category samples: 120 (30.8%)
```

## Tips

- Start with `--dry-run` to preview before inserting
- Use smaller `--samples` values for testing
- Adjust `--multi-ratio` based on your training needs
- The generator uses temperature=0.7 for diverse outputs
- Each run generates fresh, unique samples focused on TPE and longevity
- All samples include realistic data from actual TPE research studies

