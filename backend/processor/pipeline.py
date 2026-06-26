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
from backend.exporter import export_training


def _export_if_needed(conn, record_id: int, fmt: str):
    targets = conn.execute(
        "SELECT * FROM export_targets WHERE auto_export = 1 AND (format = ? OR format = 'all')",
        (fmt,),
    ).fetchall()
    for target in targets:
        already = conn.execute(
            "SELECT 1 FROM export_log WHERE target_id = ? AND record_id = ?",
            (target["id"], record_id),
        ).fetchone()
        if already:
            continue
        rows = conn.execute(
            """SELECT td.format, td.content, r.source_url, r.domain, td.record_id
               FROM training_data td JOIN records r ON r.id = td.record_id
               WHERE td.record_id = ? AND (td.format = ? OR ? = 'all')
               LIMIT 1""",
            (record_id, target["format"], target["format"]),
        ).fetchall()
        if not rows:
            continue
        export_training([dict(r) for r in rows], dict(target))
        conn.execute(
            "INSERT OR IGNORE INTO export_log (target_id, record_id) VALUES (?, ?)",
            (target["id"], record_id),
        )


def _store_training(conn, record_id: int, content: dict, fmt: str):
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


def run_pipeline(domain: str = ""):
    lake = get_lake_connection()
    main = get_main_connection()

    containers = {}
    container_formats = {}
    for row in main.execute("SELECT id, name, schema_def FROM containers").fetchall():
        containers[row["name"]] = row["id"]
        schema = json.loads(row["schema_def"])
        container_formats[row["id"]] = schema.get("training_format", "plain_text")

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

            _store_training(main, record_id, content, container_formats.get(container_id, "plain_text"))

            _export_if_needed(main, record_id, container_formats.get(container_id, "plain_text"))

    main.close()
