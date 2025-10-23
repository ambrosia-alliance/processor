ALTER TABLE effects ADD COLUMN IF NOT EXISTS deprecated BOOLEAN DEFAULT FALSE;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS deprecated_reason TEXT;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE effects ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS citation_ids JSON DEFAULT '[]';
ALTER TABLE effects ADD COLUMN IF NOT EXISTS confidence_score FLOAT;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE effects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_effects_category ON effects(category);
CREATE INDEX IF NOT EXISTS idx_effects_deprecated ON effects(deprecated);
CREATE INDEX IF NOT EXISTS idx_effects_confidence ON effects(confidence_score);

CREATE TABLE IF NOT EXISTS therapy_costs (
  id SERIAL PRIMARY KEY,
  therapy_id INTEGER NOT NULL REFERENCES therapies(id) ON DELETE CASCADE,
  amount NUMERIC,
  currency VARCHAR(10),
  context TEXT,
  citation_ids JSON DEFAULT '[]',
  confidence_score FLOAT,
  deprecated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_therapy_costs_therapy ON therapy_costs(therapy_id);
CREATE INDEX IF NOT EXISTS idx_therapy_costs_deprecated ON therapy_costs(deprecated);

CREATE TABLE IF NOT EXISTS therapy_participant_counts (
  id SERIAL PRIMARY KEY,
  therapy_id INTEGER NOT NULL REFERENCES therapies(id) ON DELETE CASCADE,
  count INTEGER,
  context TEXT,
  citation_ids JSON DEFAULT '[]',
  confidence_score FLOAT,
  deprecated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_therapy_participant_counts_therapy ON therapy_participant_counts(therapy_id);
CREATE INDEX IF NOT EXISTS idx_therapy_participant_counts_deprecated ON therapy_participant_counts(deprecated);

CREATE TABLE IF NOT EXISTS article_design_claims (
  id SERIAL PRIMARY KEY,
  article_id VARCHAR(255) NOT NULL REFERENCES article(id) ON DELETE CASCADE,
  summary TEXT,
  citation_ids JSON DEFAULT '[]',
  confidence_score FLOAT,
  deprecated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_article_design_claims_article ON article_design_claims(article_id);

CREATE TABLE IF NOT EXISTS article_sex_claims (
  id SERIAL PRIMARY KEY,
  article_id VARCHAR(255) NOT NULL REFERENCES article(id) ON DELETE CASCADE,
  summary TEXT,
  citation_ids JSON DEFAULT '[]',
  confidence_score FLOAT,
  deprecated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_article_sex_claims_article ON article_sex_claims(article_id);

CREATE TABLE IF NOT EXISTS article_age_claims (
  id SERIAL PRIMARY KEY,
  article_id VARCHAR(255) NOT NULL REFERENCES article(id) ON DELETE CASCADE,
  summary TEXT,
  citation_ids JSON DEFAULT '[]',
  confidence_score FLOAT,
  deprecated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_article_age_claims_article ON article_age_claims(article_id);

ALTER TABLE article_classification ADD COLUMN IF NOT EXISTS curated BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_article_classification_curated ON article_classification(curated);

