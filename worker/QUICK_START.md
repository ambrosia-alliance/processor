# Worker Quick Start

## Prerequisites

1. Python dependencies installed (`pip install -r requirements.txt` in processor/)
2. PostgreSQL databases configured
3. Articles in main database with `processed = false`

## Setup (One Time)

```bash
npm install

cp env.example .env

npm run db:init
```

## Run Worker

```bash
npm run dev
```

## Check Status

### Processor Health
```bash
cd ..
python classify.py --health
```

### Database Stats
```sql
psql $LOCAL_DATABASE_URL

SELECT category, COUNT(*) as count
FROM article_classifications
GROUP BY category;
```

## Environment Variables

```env
SOURCE_DATABASE_URL=postgresql://...     # Main app database
LOCAL_DATABASE_URL=postgresql://...      # Worker's database
PYTHON_PATH=python                       # Python executable
PROCESSOR_SCRIPT_PATH=../classify.py     # Classifier script
POLL_INTERVAL_MS=5000                    # Poll every 5 seconds
BATCH_SIZE=10                            # Process 10 articles at a time
```

## What It Does

1. Polls main database for unprocessed articles
2. Fetches full XML from Europe PMC
3. Calls Python classifier directly (50% confidence threshold)
4. Stores classifications locally
5. Marks articles as processed

## Logs to Watch

- Article ID and title being processed
- Sentences extracted
- Classifications found
- Total statistics

## Stop Worker

Press `Ctrl+C` for graceful shutdown

