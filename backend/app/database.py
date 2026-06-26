import sqlite3
from pathlib import Path
from typing import Optional

from backend.app.config import settings


def get_main_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.main_db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_lake_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.lake_index_db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_main_db():
    conn = get_main_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS containers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            schema_def  TEXT NOT NULL,
            extractors  TEXT NOT NULL DEFAULT '{}',
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash    TEXT NOT NULL,
            url_hash        TEXT NOT NULL,
            source_url      TEXT NOT NULL,
            domain          TEXT NOT NULL,
            container_id    INTEGER,
            extracted_data  TEXT NOT NULL,
            raw_blob_path   TEXT,
            quality_score   REAL DEFAULT 0.0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (container_id) REFERENCES containers(id)
        );

        CREATE TABLE IF NOT EXISTS container_records (
            container_id INTEGER NOT NULL,
            record_id    INTEGER NOT NULL,
            PRIMARY KEY (container_id, record_id),
            FOREIGN KEY (container_id) REFERENCES containers(id) ON DELETE CASCADE,
            FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS crawl_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            domain      TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            config      TEXT NOT NULL DEFAULT '{}',
            stats       TEXT NOT NULL DEFAULT '{}',
            started_at  TEXT,
            finished_at TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS training_data (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id       INTEGER NOT NULL,
            format          TEXT NOT NULL,
            content         TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS sources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL DEFAULT 'web',
            config          TEXT NOT NULL DEFAULT '{}',
            extractor_config TEXT NOT NULL DEFAULT '{}',
            training_format TEXT NOT NULL DEFAULT 'plain_text',
            enabled         INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS export_targets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL DEFAULT 'jsonl',
            config          TEXT NOT NULL DEFAULT '{}',
            format          TEXT NOT NULL DEFAULT 'plain_text',
            auto_export     INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS export_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id       INTEGER NOT NULL,
            record_id       INTEGER NOT NULL,
            exported_at     TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (target_id) REFERENCES export_targets(id) ON DELETE CASCADE,
            FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE,
            UNIQUE(target_id, record_id)
        );

        CREATE TABLE IF NOT EXISTS validation_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id       INTEGER NOT NULL,
            action          TEXT NOT NULL,
            notes           TEXT DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS datasets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            description     TEXT DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS dataset_records (
            dataset_id      INTEGER NOT NULL,
            record_id       INTEGER NOT NULL,
            PRIMARY KEY (dataset_id, record_id),
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS dead_letter (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            url             TEXT NOT NULL,
            domain          TEXT NOT NULL,
            reason          TEXT NOT NULL,
            metadata        TEXT NOT NULL DEFAULT '{}',
            crawl_session_id INTEGER,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS analysis_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id        INTEGER NOT NULL,
            record_index    INTEGER NOT NULL,
            format          TEXT DEFAULT '',
            content_sample  TEXT DEFAULT '',
            word_count      INTEGER DEFAULT 0,
            char_count      INTEGER DEFAULT 0,
            est_token_count INTEGER DEFAULT 0,
            has_title       INTEGER DEFAULT 0,
            has_code        INTEGER DEFAULT 0,
            has_qa          INTEGER DEFAULT 0,
            section_count   INTEGER DEFAULT 0,
            has_instruction INTEGER DEFAULT 0,
            has_response    INTEGER DEFAULT 0,
            line_count      INTEGER DEFAULT 0,
            quality_score   REAL DEFAULT 0.0,
            is_reformattable INTEGER DEFAULT 0,
            flags           TEXT DEFAULT '[]',
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS analysis_batches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            filename        TEXT NOT NULL,
            total_records   INTEGER DEFAULT 0,
            high_value      INTEGER DEFAULT 0,
            reformattable   INTEGER DEFAULT 0,
            avg_quality     REAL DEFAULT 0.0,
            summary         TEXT DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS proxies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            address     TEXT NOT NULL UNIQUE,
            enabled     INTEGER NOT NULL DEFAULT 1,
            failures    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def migrate_main_db():
    """Add columns introduced after initial schema creation."""
    conn = get_main_connection()
    for col in ["status", "validated_by", "validated_at", "reviewer_notes", "source_id"]:
        try:
            conn.execute(f"ALTER TABLE records ADD COLUMN {col} TEXT DEFAULT ''")
        except Exception:
            pass
    for col in ["similarity_hash"]:
        try:
            conn.execute(f"ALTER TABLE records ADD COLUMN {col} TEXT DEFAULT ''")
        except Exception:
            pass
    for col in ["refiner_config"]:
        try:
            conn.execute(f"ALTER TABLE sources ADD COLUMN {col} TEXT DEFAULT '{{}}'")
        except Exception:
            pass
    conn.commit()
    conn.close()


def init_lake_db():
    conn = get_lake_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS blobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path       TEXT NOT NULL UNIQUE,
            url_hash        TEXT NOT NULL,
            content_hash    TEXT,
            original_url    TEXT NOT NULL,
            domain          TEXT NOT NULL,
            http_status     INTEGER,
            headers         TEXT,
            proxy_used      TEXT,
            crawl_session_id INTEGER,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS url_frontier (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            url             TEXT NOT NULL,
            domain          TEXT NOT NULL,
            depth           INTEGER DEFAULT 0,
            status          TEXT NOT NULL DEFAULT 'pending',
            crawl_session_id INTEGER,
            retries         INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_blobs_url_hash ON blobs(url_hash);
        CREATE INDEX IF NOT EXISTS idx_blobs_content_hash ON blobs(content_hash);
        CREATE INDEX IF NOT EXISTS idx_frontier_status ON url_frontier(status);
    """)
    conn.commit()
    conn.close()
