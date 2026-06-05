PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    price_yen INTEGER NOT NULL,
    concerns TEXT NOT NULL,
    tags TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS product_fts USING fts5(
    product_id UNINDEXED,
    name,
    brand,
    category,
    concerns,
    tags,
    description
);

CREATE TABLE IF NOT EXISTS beauty_memos (
    memo_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    concerns TEXT NOT NULL,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skin_logs (
    skin_log_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    questionnaire_json TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    recommendation_json TEXT
);

