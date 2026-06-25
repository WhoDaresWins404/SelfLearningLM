import json
from pathlib import Path

from backend.app.config import settings
from backend.app.database import get_main_connection, get_lake_connection
from backend.processor.analyzer import analyze_blob
from backend.processor.extractors import extract
from backend.processor.deduplicator import is_duplicate
from backend.processor.qualifier import score
from backend.processor.refiner import refine
from backend.processor.storage_writer import write_record


def run_pipeline(domain: str = ""):
    lake = get_lake_connection()
    main = get_main_connection()

    containers = {row["name"]: row["id"] for row in main.execute("SELECT id, name FROM containers").fetchall()}

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

        matched = analyze_blob(html)
        if not matched:
            continue

        for container_name in matched:
            container_id = containers.get(container_name)
            if not container_id:
                continue

            extracted = extract(container_name, html)
            if not extracted:
                continue

            refined = refine(extracted)
            quality = score(refined)

            write_record(
                url=blob["original_url"],
                domain=blob["domain"],
                extracted=refined,
                container_id=container_id,
                raw_blob_path=str(file_path),
                quality_score=quality,
            )

    main.close()
