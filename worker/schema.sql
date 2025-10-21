CREATE TABLE IF NOT EXISTS article_classifications (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL,
    article_title TEXT,
    therapy_id INTEGER NOT NULL,
    sentence_text TEXT NOT NULL,
    sentence_idx INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    model_version VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_article_classifications_article ON article_classifications(article_id);
CREATE INDEX IF NOT EXISTS idx_article_classifications_category ON article_classifications(category);
CREATE INDEX IF NOT EXISTS idx_article_classifications_therapy ON article_classifications(therapy_id);
CREATE INDEX IF NOT EXISTS idx_article_classifications_confidence ON article_classifications(confidence);

CREATE TABLE IF NOT EXISTS processing_log (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    sentences_processed INTEGER DEFAULT 0,
    classifications_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_processing_log_article ON processing_log(article_id);
CREATE INDEX IF NOT EXISTS idx_processing_log_status ON processing_log(status);

