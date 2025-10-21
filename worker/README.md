# Article Processor Worker

Worker service that processes articles from Europe PMC through the therapy classification pipeline.

## Overview

This worker:
1. Polls the main database for unprocessed articles
2. Fetches full text XML from Europe PMC
3. Calls the Python classifier directly via subprocess
4. Stores classifications in a local PostgreSQL database
5. Marks articles as processed

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Edit `.env`:
- `SOURCE_DATABASE_URL`: Main application database (read articles)
- `LOCAL_DATABASE_URL`: Worker's local database (store classifications)
- `PYTHON_PATH`: Path to Python executable (default: python)
- `PROCESSOR_SCRIPT_PATH`: Path to classify.py script (default: ../classify.py)
- `POLL_INTERVAL_MS`: How often to check for new articles (default: 5000ms)
- `BATCH_SIZE`: How many articles to process per batch (default: 10)

### 3. Initialize Local Database

```bash
npm run db:init
```

### 4. Install Python Dependencies

In the processor directory:

```bash
cd ..
pip install -r requirements.txt
```

## Running

### Development

```bash
npm run dev
```

### Production

```bash
npm run build
npm start
```

## Architecture

```
Main DB (articles) → Worker → Python Script (subprocess) → Worker Local DB (classifications)
```

## Database Schema

### article_classifications

Stores individual sentence classifications with category and confidence scores.

### processing_log

Tracks processing status for each article.

