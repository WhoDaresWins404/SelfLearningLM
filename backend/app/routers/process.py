import threading

from fastapi import APIRouter

from backend.app.database import get_main_connection, get_lake_connection
from backend.processor.pipeline import run_pipeline

router = APIRouter(prefix="/api/process", tags=["process"])

_state = {"running": False, "last_status": "", "last_domain": "", "last_error": "", "records_before": 0, "records_after": 0}


def _run(domain: str):
    _state["running"] = True
    _state["last_domain"] = domain
    _state["last_error"] = ""
    try:
        conn = get_main_connection()
        _state["records_before"] = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        conn.close()
        run_pipeline(domain=domain)
        conn = get_main_connection()
        _state["records_after"] = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        conn.close()
        _state["last_status"] = "completed"
    except Exception as e:
        _state["last_status"] = "failed"
        _state["last_error"] = str(e)
    finally:
        _state["running"] = False


@router.post("", status_code=202)
def start_processing(domain: str = ""):
    if _state["running"]:
        return {"status": "already_running"}
    thread = threading.Thread(target=_run, args=(domain,), daemon=True)
    thread.start()
    return {"status": "started", "domain": domain or "all"}


@router.get("/status")
def processing_status():
    return {
        "running": _state["running"],
        "status": _state["last_status"],
        "domain": _state["last_domain"],
        "error": _state["last_error"],
        "records_before": _state["records_before"],
        "records_after": _state["records_after"],
    }


@router.get("/domains")
def available_domains():
    lake = get_lake_connection()
    rows = lake.execute("SELECT DISTINCT domain FROM blobs ORDER BY domain").fetchall()
    lake.close()
    return [r["domain"] for r in rows]
