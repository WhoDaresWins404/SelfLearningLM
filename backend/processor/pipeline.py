import json
from pathlib import Path

from backend.app.config import settings
from backend.app.database import get_main_connection, get_lake_connection
from backend.processor.analyzer import analyze_blob
from backend.processor.content_extractor import extract_content
from backend.processor.deduplicator import is_duplicate
from backend.processor.extractors import extract
from backend.processor.qualifier import score
from backend.processor.refiner import refine
from backend.processor.storage_writer import write_record
from backend.processor.training_formatter import FORMATTERS


def _store_training(record_id: int, content: dict, container_id: int):
    conn = get_main_connection()
    row = conn.execute("SELECT schema_def FROM containers WHERE id = ?", (container_id,)).fetchone()
    if not row:
        conn.close()
        return
    schema = json.loads(row["schema_def"])
    fmt = schema.get("training_format", "plain_text")
    conn.close()

    conn = get_main_connection()
    if fmt == "all":
        for name in FORMATTERS:
            formatted = FORMATTERS[name](content)
            conn.execute(
                "INSERT INTO training_data (record_id, format, content) VALUES (?, ?, ?)",
                (record_id, name, formatted),
            )
    else:
        formatter = FORMATTERS.get(fmt, FORMATTERS["plain_text"])
        formatted = formatter(content)
        conn.execute(
            "INSERT INTO training_data (record_id, format, content) VALUES (?, ?, ?)",
            (record_id, fmt, formatted),
        )
    conn.commit()
    conn.close()


def run_pipeline(domain: str = ""):
    lake = get_lake_connection()
    main = get_main_connection()

    containers = {row["name"]: row["id"] for row in main.execute("SELECT id, name FROM containers").fetchall()}
    container_schemas = {row["name"]: json.loads(row["schema_def"]) for row in main.execute("SELECT name, schema_def FROM containers").fetchall()}

    query = "SELECT * FROM blobs"
    params = []
    if domain:
        query += " WHERE domain = ?"
        params.append(domain)

    blobs = lake.execute(query, params).fetchall()
    lake.close()

    for blob in blobs:
        file_path = Path(blob["file_path"])
        if not file_path.exists():
            continue

        html = file_path.read_text(encoding="utf-8")

        if is_duplicate(blob["original_url"], html):
            continue

        content = extract_content(html)

        if not content.get("clean_text"):
            continue

        matched = analyze_blob(html)
        if not matched:
            continue

        for container_name in matched:
            container_id = containers.get(container_name)
            if not container_id:
                continue

            extracted = extract(container_name, html)
            refined = refine(extracted) if extracted else {}
            quality = score(refined)

            record_id = write_record(
                url=blob["original_url"],
                domain=blob["domain"],
                extracted=refined,
                container_id=container_id,
                raw_blob_path=str(file_path),
                quality_score=quality,
            )

            _store_training(record_id, content, container_id)

    main.close()
