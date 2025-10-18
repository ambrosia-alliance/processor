# Therapy Classification API

A REST API service that processes medical therapy text through zero-shot classification using BART-MNLI, returning aggregated category summaries.

## Features

- Sentence-level text chunking
- Zero-shot classification into 13 therapy-related categories
- Aggregated results with confidence scores
- PyTorch Lightning integration
- FastAPI REST endpoints

## Categories

The API classifies text into the following categories:

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
```

## Usage

Start the API server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /classify

Classify therapy text into categories.

**Request:**
```json
{
  "text": "The therapeutic plasma exchange showed a 75% success rate in treating the condition. Patients experienced mild side effects including fatigue. The trial included 150 participants aged 40-65 years."
}
```

**Response:**
```json
{
  "categories": {
    "efficacy_rate": {
      "count": 1,
      "avg_confidence": 0.92,
      "sentences": [
        {
          "text": "The therapeutic plasma exchange showed a 75% success rate in treating the condition.",
          "confidence": 0.92
        }
      ]
    },
    "side_effect_severity": {
      "count": 1,
      "avg_confidence": 0.88,
      "sentences": [...]
    }
  }
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model": "facebook/bart-large-mnli",
  "device": "cpu"
}
```

### GET /categories

List all available classification categories.

**Response:**
```json
{
  "categories": ["efficacy_extent", "efficacy_rate", ...]
}
```

## Configuration

Edit `.env` file to configure:

- `MODEL_NAME`: HuggingFace model name
- `CONFIDENCE_THRESHOLD`: Minimum confidence score
- `MIN_SENTENCE_LENGTH`: Minimum sentence length to process

## Architecture

- **FastAPI**: REST API framework
- **PyTorch Lightning**: ML model wrapper
- **BART-MNLI**: Zero-shot classification model
- **NLTK**: Sentence tokenization

