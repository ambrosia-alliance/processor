-- Narrow schema: therapy-level effects with 0..n citations, articles tied to therapy
-- Portable JSON arrays for citations (Postgres JSONB/MySQL JSON)

-- 1) Therapies (incl. cost)
CREATE TABLE therapies (
  id                SERIAL PRIMARY KEY,
  name              VARCHAR(200) NOT NULL UNIQUE,
  cost_summary      TEXT,
  cost_currency     VARCHAR(10),
  cost_amount       DECIMAL(12,2),
  cost_citation_ids JSON DEFAULT '[]',
  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (cost_summary IS NULL OR jsonb_array_length(cost_citation_ids::jsonb) > 0)
);

-- 2) Articles (each article belongs to one therapy)
CREATE TABLE articles (
  id            SERIAL PRIMARY KEY,
  therapy_id    INTEGER NOT NULL REFERENCES therapies(id) ON DELETE CASCADE,
  title         VARCHAR(500) NOT NULL,
  journal       VARCHAR(300),
  year          INTEGER,
  url           VARCHAR(2048),
  doi           VARCHAR(200)
);

-- 3) Citations (reference articles)
CREATE TABLE citations (
  id            SERIAL PRIMARY KEY,
  quote_text    TEXT,
  article_id    INTEGER REFERENCES articles(id) ON DELETE CASCADE,
  locator       VARCHAR(200)
);

CREATE TABLE article_details (
  article_id                 INTEGER PRIMARY KEY REFERENCES articles(id) ON DELETE CASCADE,
  design_summary             TEXT,
  design_citation_ids        JSON DEFAULT '[]',
  participants_total         INTEGER,
  participants_citation_ids  JSON DEFAULT '[]',
  sex_summary                TEXT,
  sex_citation_ids           JSON DEFAULT '[]',
  age_summary                TEXT,
  age_citation_ids           JSON DEFAULT '[]',
  created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (design_summary IS NULL OR jsonb_array_length(design_citation_ids::jsonb) > 0),
  CHECK (participants_total IS NULL OR jsonb_array_length(participants_citation_ids::jsonb) > 0),
  CHECK (sex_summary IS NULL OR jsonb_array_length(sex_citation_ids::jsonb) > 0),
  CHECK (age_summary IS NULL OR jsonb_array_length(age_citation_ids::jsonb) > 0)
);

-- 4) Effects catalogue (explicit rows; no article linkage here)
CREATE TABLE effects (
  id           SERIAL PRIMARY KEY,
  therapy_id                       INTEGER NOT NULL REFERENCES therapies(id) ON DELETE CASCADE,
  name                             VARCHAR(200) NOT NULL,
  UNIQUE(therapy_id, name),

  efficacy_extent_summary          TEXT,
  efficacy_extent_citation_ids     JSON DEFAULT '[]',

  efficacy_rate_summary            TEXT,
  efficacy_rate_citation_ids       JSON DEFAULT '[]',

  side_effect_severity_summary     TEXT,
  side_effect_severity_citation_ids JSON DEFAULT '[]',
  side_effect_risk_summary         TEXT,
  side_effect_risk_citation_ids    JSON DEFAULT '[]',

  participants_total               INTEGER,
  sex_summary                      TEXT,
  age_summary                      TEXT,
  design_summaries                 JSON DEFAULT '[]',
  CHECK (efficacy_extent_summary IS NULL OR jsonb_array_length(efficacy_extent_citation_ids::jsonb) > 0),
  CHECK (efficacy_rate_summary IS NULL OR jsonb_array_length(efficacy_rate_citation_ids::jsonb) > 0),
  CHECK (side_effect_severity_summary IS NULL OR jsonb_array_length(side_effect_severity_citation_ids::jsonb) > 0),
  CHECK (side_effect_risk_summary IS NULL OR jsonb_array_length(side_effect_risk_citation_ids::jsonb) > 0)
);


CREATE INDEX idx_effects_by_therapy ON effects(therapy_id);
CREATE INDEX idx_effects_by_name    ON effects(name);

CREATE TABLE article_classifications (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL,
    therapy_id INTEGER NOT NULL REFERENCES therapies(id) ON DELETE CASCADE,
    sentence_text TEXT NOT NULL,
    sentence_idx INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    model_version VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_article_classifications_article ON article_classifications(article_id);
CREATE INDEX idx_article_classifications_category ON article_classifications(category);
CREATE INDEX idx_article_classifications_therapy ON article_classifications(therapy_id);
CREATE INDEX idx_article_classifications_confidence ON article_classifications(confidence);

CREATE TABLE processing_log (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    sentences_processed INTEGER DEFAULT 0,
    classifications_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_processing_log_article ON processing_log(article_id);
CREATE INDEX idx_processing_log_status ON processing_log(status);
