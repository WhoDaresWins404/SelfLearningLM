import hashlib
import json

from backend.app.database import get_main_connection


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_record(url: str, domain: str, extracted: dict, container_id: int,
                 raw_blob_path: str = "", quality_score: float = 0.0) -> int:
    conn = get_main_connection()
    content_hash = _hash(json.dumps(extracted, sort_keys=True))
    url_hash = _hash(url)

    cur = conn.execute(
        """INSERT INTO records
           (content_hash, url_hash, source_url, domain, container_id, extracted_data, raw_blob_path, quality_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (content_hash, url_hash, url, domain, container_id, json.dumps(extracted), raw_blob_path, quality_score),
    )
    record_id = cur.lastrowid

    conn.execute(
        "INSERT OR IGNORE INTO container_records (container_id, record_id) VALUES (?, ?)",
        (container_id, record_id),
    )
    conn.commit()
    conn.close()
    return record_id
