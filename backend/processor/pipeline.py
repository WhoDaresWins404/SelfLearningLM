import json
import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup

from backend.app.database import get_main_connection, get_lake_connection
from backend.processor.content_extractor import extract_content
from backend.processor.training_formatter import FORMATTERS
from backend.processor.cleanup import refine_formatted_content

_STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
               "have", "has", "had", "do", "does", "did", "but", "if", "or", "and",
               "in", "on", "at", "to", "for", "of", "with", "by", "from", "as"}

_AUTO_REJECT_THRESHOLD = 20.0


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _simhash(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    v = [0] * 64
    for w in words:
        h = hash(w)
        for i in range(64):
            bit = (h >> i) & 1
            v[i] += 1 if bit else -1
    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= 1 << i
    return fingerprint


def _hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _is_near_duplicate(content: str, conn, threshold: int = 8) -> bool:
    fprint = _simhash(content)
    rows = conn.execute("SELECT id, similarity_hash FROM records WHERE similarity_hash IS NOT NULL AND similarity_hash != ''").fetchall()
    for r in rows:
        try:
            existing = int(r["similarity_hash"])
            if _hamming_distance(fprint, existing) <= threshold:
                return True
        except (ValueError, TypeError):
            continue
    return False


def _is_processed(url: str, html: str) -> bool:
    url_hash = _hash(url)
    content_hash = _hash(html)
    conn = get_main_connection()
    row = conn.execute(
        "SELECT 1 FROM records WHERE url_hash = ? OR content_hash = ? LIMIT 1",
        (url_hash, content_hash),
    ).fetchone()
    conn.close()
    return row is not None


def _score(content: dict) -> float:
    score = 50.0
    text_length = content.get("word_count", 0)
    if text_length > 500:
        score += 20
    elif text_length > 100:
        score += 10
    if content.get("has_code"):
        score += 10
    if content.get("title"):
        score += 10
    if content.get("is_raw_dump"):
        score -= 40

    text = content.get("clean_text", "")
    if text:
        total_chars = len(text)
        alnum = sum(1 for c in text if c.isalnum() or c.isspace())
        punct = sum(1 for c in text if c in ".,!?;:()[]{}\"'")
        if total_chars > 0:
            punct_density = punct / total_chars
            if punct_density > 0.3:
                score -= 15
            elif punct_density < 0.01 and total_chars > 200:
                score -= 10
            alnum_ratio = alnum / total_chars
            if alnum_ratio < 0.5:
                score -= 20

        words = text.lower().split()
        if words:
            stop_ratio = sum(1 for w in words if w in _STOP_WORDS) / len(words)
            if stop_ratio < 0.05 and len(words) > 50:
                score -= 15
            if stop_ratio > 0.5:
                score -= 10

    return max(0.0, min(100.0, round(score, 1)))


def _extract_fields(html: str, extractor_config: dict) -> dict:
    soup = BeautifulSoup(html, "lxml")
    result = {}
    for field in extractor_config.get("fields", []):
        name = field.get("name")
        selector = field.get("selector", "")
        sel_type = field.get("type", "css")
        multiple = field.get("multiple", False)
        if not name or not selector:
            continue
        if sel_type == "css":
            if multiple:
                tags = soup.select(selector)
                result[name] = [t.get_text(strip=True) for t in tags if t.get_text(strip=True)]
            else:
                tag = soup.select_one(selector)
                result[name] = tag.get_text(strip=True) if tag else ""
        elif sel_type == "regex":
            matches = re.findall(selector, html, re.I)
            result[name] = matches if multiple else (matches[0] if matches else "")
        elif sel_type == "attr":
            tag = soup.select_one(selector.get("tag", "*"))
            attr = selector.get("attr", "")
            result[name] = tag.get(attr, "") if tag else ""
    return result


def _store_training(conn, record_id: int, content: dict, fmt: str, refiner_config: dict | None = None):
    raw_content = content
    if fmt == "all":
        for name in FORMATTERS:
            formatted = FORMATTERS[name](raw_content)
            if refiner_config and refiner_config.get(name, True):
                formatted = refine_formatted_content(formatted, name)
            conn.execute(
                "INSERT INTO training_data (record_id, format, content) VALUES (?, ?, ?)",
                (record_id, name, formatted),
            )
    else:
        formatter = FORMATTERS.get(fmt, FORMATTERS["plain_text"])
        formatted = formatter(raw_content)
        if refiner_config and refiner_config.get(fmt, True):
            formatted = refine_formatted_content(formatted, fmt)
        conn.execute(
            "INSERT INTO training_data (record_id, format, content) VALUES (?, ?, ?)",
            (record_id, fmt, formatted),
        )


def _export_if_needed(conn, record_id: int, fmt: str):
    from backend.exporter import export_training
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


def _parse_refiner_config(source: dict | None) -> tuple[list[str] | None, int | None, dict | None, dict | None]:
    extra_boilerplate = None
    min_quality = None
    refiner_flags = None
    word_fixes = None
    if source:
        try:
            config = json.loads(source["config"]) if isinstance(source["config"], str) else source["config"]
            extra_boilerplate = config.get("boilerplate_patterns") or None
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            refiner_config = json.loads(source.get("refiner_config", "{}")) if isinstance(source.get("refiner_config"), str) else source.get("refiner_config", {})
            if isinstance(refiner_config, dict):
                extra_boilerplate = refiner_config.get("boilerplate_patterns") or extra_boilerplate
                min_quality = refiner_config.get("min_quality")
                word_fixes = refiner_config.get("word_fixes")
                refiner_flags = {k: v for k, v in refiner_config.items() if k in ("instruction_response", "code_explanation", "qa", "plain_text", "all")}
        except (json.JSONDecodeError, TypeError):
            pass
    return extra_boilerplate, min_quality, refiner_flags, word_fixes


def run_pipeline(domain: str = ""):
    lake = get_lake_connection()
    main = get_main_connection()

    sources = {}
    for row in main.execute("SELECT * FROM sources WHERE enabled = 1").fetchall():
        config = json.loads(row["config"])
        source_domain = config.get("domain", row["name"])
        sources[source_domain] = dict(row)

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

        if _is_processed(blob["original_url"], html):
            continue

        source = sources.get(blob["domain"])
        extra_bp, min_qual, refiner_flags, word_fixes = _parse_refiner_config(source)

        content = extract_content(html, extra_boilerplate=extra_bp, custom_word_fixes=word_fixes)
        if not content.get("clean_text"):
            continue

        if _is_near_duplicate(content["clean_text"], main):
            continue

        if source:
            extractor_config = json.loads(source["extractor_config"])
            fields = _extract_fields(html, extractor_config)
            content["_extracted"] = fields

        quality = _score(content)

        if min_qual is not None and quality < min_qual:
            continue

        url_hash = _hash(blob["original_url"])
        content_hash = _hash(html)
        source_id = source["id"] if source else None
        simhash_val = str(_simhash(content.get("clean_text", "")))

        status = "pending" if quality >= _AUTO_REJECT_THRESHOLD else "rejected"

        cur = main.execute(
            """INSERT INTO records
               (content_hash, url_hash, source_url, domain, source_id, extracted_data, raw_blob_path, quality_score, status, similarity_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (content_hash, url_hash, blob["original_url"], blob["domain"],
             source_id, json.dumps(content), str(file_path), quality, status, simhash_val),
        )
        record_id = cur.lastrowid

        if status == "pending":
            fmt = source["training_format"] if source else "plain_text"
            _store_training(main, record_id, content, fmt, refiner_flags)
            _export_if_needed(main, record_id, fmt)

    main.commit()
    main.close()


def backfill_training_data(domain: str = ""):
    conn = get_main_connection()
    params = []
    query = """SELECT r.id, r.domain, r.source_id
               FROM records r
               WHERE r.id NOT IN (SELECT record_id FROM training_data) AND r.status = 'approved'"""
    if domain:
        query += " AND r.domain = ?"
        params.append(domain)
    rows = conn.execute(query, params).fetchall()
    sources = {}
    for row in conn.execute("SELECT * FROM sources").fetchall():
        sources[row["id"]] = dict(row)
    count = 0
    for row in rows:
        source = sources.get(row["source_id"])
        fmt = source["training_format"] if source else "plain_text"
        _, _, refiner_flags, word_fixes = _parse_refiner_config(source)
        rec = conn.execute("SELECT raw_blob_path FROM records WHERE id = ?", (row["id"],)).fetchone()
        if not rec or not rec["raw_blob_path"]:
            continue
        file_path = Path(rec["raw_blob_path"])
        if not file_path.exists():
            continue
        html = file_path.read_text(encoding="utf-8", errors="replace")
        content = extract_content(html, custom_word_fixes=word_fixes)
        if not content.get("clean_text"):
            continue
        _store_training(conn, row["id"], content, fmt, refiner_flags)
        _export_if_needed(conn, row["id"], fmt)
        count += 1
    conn.commit()
    conn.close()
    return count


def reextract_records(domain: str = "") -> int:
    conn = get_main_connection()
    sources = {}
    for row in conn.execute("SELECT * FROM sources").fetchall():
        sources[row["id"]] = dict(row)

    params = []
    query = "SELECT id, raw_blob_path, source_id, domain, source_url FROM records WHERE raw_blob_path IS NOT NULL AND raw_blob_path != ''"
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    rows = conn.execute(query, params).fetchall()
    conn.close()

    count = 0
    for row in rows:
        file_path = Path(row["raw_blob_path"])
        if not file_path.exists():
            continue
        html = file_path.read_text(encoding="utf-8", errors="replace")
        source = sources.get(row["source_id"])
        extra_bp, min_qual, refiner_flags, word_fixes = _parse_refiner_config(source)
        content = extract_content(html, extra_boilerplate=extra_bp, custom_word_fixes=word_fixes)
        if not content.get("clean_text"):
            continue

        if source:
            extractor_config = json.loads(source["extractor_config"])
            fields = _extract_fields(html, extractor_config)
            content["_extracted"] = fields

        quality = _score(content)
        content_hash = _hash(html)
        url_hash = _hash(row["source_url"] or html[:200])
        fmt = source["training_format"] if source else "plain_text"
        simhash_val = str(_simhash(content.get("clean_text", "")))
        status = "pending" if quality >= _AUTO_REJECT_THRESHOLD else "rejected"

        conn2 = get_main_connection()
        conn2.execute(
            "UPDATE records SET extracted_data = ?, quality_score = ?, content_hash = ?, url_hash = ?, similarity_hash = ?, status = ? WHERE id = ?",
            (json.dumps(content), quality, content_hash, url_hash, simhash_val, status, row["id"]),
        )
        conn2.execute("DELETE FROM training_data WHERE record_id = ?", (row["id"],))
        if status == "pending":
            _store_training(conn2, row["id"], content, fmt, refiner_flags)
            _export_if_needed(conn2, row["id"], fmt)
        conn2.commit()
        conn2.close()
        count += 1
    return count
