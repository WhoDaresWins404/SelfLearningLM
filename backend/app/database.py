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

        CREATE TABLE IF NOT EXISTS dead_letter (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            url             TEXT NOT NULL,
            domain          TEXT NOT NULL,
            reason          TEXT NOT NULL,
            metadata        TEXT NOT NULL DEFAULT '{}',
            crawl_session_id INTEGER,
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
