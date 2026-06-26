import json

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse

from backend.app.database import get_main_connection
from backend.processor.analyzer import analyze_jsonl

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/import")
async def import_analysis(file: UploadFile = File(...)):
    if not file.filename.endswith(".jsonl"):
        raise HTTPException(400, "Only .jsonl files are accepted")
    raw = (await file.read()).decode("utf-8")
    result = analyze_jsonl(raw, file.filename)

    conn = get_main_connection()
    cur = conn.execute(
        "INSERT INTO analysis_batches (filename, total_records, high_value, reformattable, avg_quality, summary) VALUES (?, ?, ?, ?, ?, ?)",
        (
            result["summary"]["filename"],
            result["summary"]["total_records"],
            result["summary"]["high_value"],
            result["summary"]["reformattable"],
            result["summary"]["avg_quality"],
            result["summary"]["summary"],
        ),
    )
    batch_id = cur.lastrowid

    for r in result["results"]:
        conn.execute(
            """INSERT INTO analysis_results
               (batch_id, record_index, format, content_sample, word_count, char_count,
                est_token_count, has_title, has_code, has_qa, section_count,
                has_instruction, has_response, line_count, quality_score,
                is_reformattable, flags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                batch_id,
                r["record_index"],
                r["format"],
                r["content_sample"],
                r["word_count"],
                r["char_count"],
                r["est_token_count"],
                r["has_title"],
                r["has_code"],
                r["has_qa"],
                r["section_count"],
                r["has_instruction"],
                r["has_response"],
                r["line_count"],
                r["quality_score"],
                r["is_reformattable"],
                r["flags"],
            ),
        )
    conn.commit()
    conn.close()

    conn = get_main_connection()
    batch = dict(conn.execute("SELECT * FROM analysis_batches WHERE id = ?", (batch_id,)).fetchone())
    conn.close()
    return batch


@router.get("/batches")
def list_batches():
    conn = get_main_connection()
    rows = conn.execute("SELECT * FROM analysis_batches ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/batches/{batch_id}")
def get_batch(batch_id: int):
    conn = get_main_connection()
    batch = conn.execute("SELECT * FROM analysis_batches WHERE id = ?", (batch_id,)).fetchone()
    if not batch:
        conn.close()
        raise HTTPException(404, "Batch not found")
    results = conn.execute(
        "SELECT * FROM analysis_results WHERE batch_id = ? ORDER BY record_index",
        (batch_id,),
    ).fetchall()
    conn.close()
    return {"batch": dict(batch), "results": [dict(r) for r in results]}


@router.get("/batches/{batch_id}/export")
def export_batch_report(batch_id: int):
    conn = get_main_connection()
    batch = conn.execute("SELECT * FROM analysis_batches WHERE id = ?", (batch_id,)).fetchone()
    if not batch:
        conn.close()
        raise HTTPException(404, "Batch not found")
    results = conn.execute(
        "SELECT * FROM analysis_results WHERE batch_id = ? ORDER BY record_index",
        (batch_id,),
    ).fetchall()
    conn.close()

    lines = [json.dumps({
        "summary": dict(batch),
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }, ensure_ascii=False)]
    lines.append("")
    for r in results:
        lines.append(json.dumps(dict(r), ensure_ascii=False))
    return PlainTextResponse("\n".join(lines), media_type="application/jsonl")
