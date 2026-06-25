import logging
import time

logger = logging.getLogger("crawl_tracker")

_active_crawls: dict[int, dict] = {}


def init_session(session_id: int, total_pages: int):
    _active_crawls[session_id] = {
        "current_url": "",
        "last_activity": time.time(),
        "pages_crawled": 0,
        "total_pages": total_pages,
    }
    logger.info("Tracker initialized for session %s", session_id)


def set_current_url(session_id: int, url: str):
    record = _active_crawls.get(session_id)
    if record is None:
        logger.warning("set_current_url: no tracker record for session %s", session_id)
        record = _active_crawls.setdefault(session_id, {})
    record["current_url"] = url
    record["last_activity"] = time.time()


def get_status(session_id: int) -> dict:
    record = _active_crawls.get(session_id)
    if not record:
        return {"current_url": "", "last_activity": 0, "alive": False, "pages_crawled": 0, "total_pages": 0}
    return {
        "current_url": record.get("current_url", ""),
        "last_activity": record.get("last_activity", 0),
        "alive": (time.time() - record.get("last_activity", 0)) < 30,
        "pages_crawled": record.get("pages_crawled", 0),
        "total_pages": record.get("total_pages", 0),
    }


def remove_session(session_id: int):
    _active_crawls.pop(session_id, None)


def set_progress(session_id: int, pages_crawled: int, total: int):
    record = _active_crawls.get(session_id)
    if record is None:
        logger.warning("set_progress: no tracker record for session %s", session_id)
        record = _active_crawls.setdefault(session_id, {})
    record["pages_crawled"] = pages_crawled
    record["total_pages"] = total
    record["last_activity"] = time.time()
