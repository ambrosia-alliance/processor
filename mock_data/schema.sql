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

-- Example: fetch all citations backing a specific effect's efficacy_rate
-- Postgres
-- SELECT c.*
-- FROM effects e
-- JOIN LATERAL (
--   SELECT (jsonb_array_elements_text(e.efficacy_rate_citation_ids)::int) AS cid
-- ) j ON TRUE
-- JOIN citations c ON c.id = j.cid
-- WHERE e.therapy_id = :t AND e.name = 'efficacy_rate';

-- MySQL
-- SELECT c.*
-- FROM effects e
-- JOIN JSON_TABLE(e.efficacy_rate_citation_ids, '$[*]' COLUMNS (cid INT PATH '$')) jt ON TRUE
-- JOIN citations c ON c.id = jt.cid
-- WHERE e.therapy_id = :t AND e.name = 'efficacy_rate';
