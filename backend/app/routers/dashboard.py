from fastapi import APIRouter

from backend.app.database import get_main_connection, get_lake_connection

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard():
    main = get_main_connection()
    lake = get_lake_connection()

    total_records = main.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    pending = main.execute("SELECT COUNT(*) FROM records WHERE status = 'pending'").fetchone()[0]
    approved = main.execute("SELECT COUNT(*) FROM records WHERE status = 'approved'").fetchone()[0]
    rejected = main.execute("SELECT COUNT(*) FROM records WHERE status = 'rejected'").fetchone()[0]
    dead_letter_count = main.execute("SELECT COUNT(*) FROM dead_letter").fetchone()[0]
    blob_count = lake.execute("SELECT COUNT(*) FROM blobs").fetchone()[0]
    pending_urls = lake.execute("SELECT COUNT(*) FROM url_frontier WHERE status = 'pending'").fetchone()[0]
    active_crawls = main.execute("SELECT COUNT(*) FROM crawl_sessions WHERE status = 'running'").fetchone()[0]
    training_count = main.execute("SELECT COUNT(*) FROM training_data").fetchone()[0]
    dataset_count = main.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]

    recent_records = main.execute(
        "SELECT id, domain, quality_score, status, created_at FROM records ORDER BY created_at DESC LIMIT 10"
    ).fetchall()

    main.close()
    lake.close()

    return {
        "total_records": total_records,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "dead_letter_count": dead_letter_count,
        "blob_count": blob_count,
        "pending_urls": pending_urls,
        "active_crawls": active_crawls,
        "training_count": training_count,
        "dataset_count": dataset_count,
        "recent_records": [dict(r) for r in recent_records],
    }
