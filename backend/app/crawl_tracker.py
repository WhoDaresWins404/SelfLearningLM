import time

_active_crawls: dict[int, dict] = {}


def set_current_url(session_id: int, url: str):
    record = _active_crawls.setdefault(session_id, {})
    record["current_url"] = url
    record["last_activity"] = time.time()


def get_status(session_id: int) -> dict:
    record = _active_crawls.get(session_id)
    if not record:
        return {"current_url": "", "last_activity": 0, "alive": False}
    return {
        "current_url": record.get("current_url", ""),
        "last_activity": record.get("last_activity", 0),
        "alive": (time.time() - record.get("last_activity", 0)) < 30,
    }


def remove_session(session_id: int):
    _active_crawls.pop(session_id, None)


def set_progress(session_id: int, pages_crawled: int, total: int):
    record = _active_crawls.setdefault(session_id, {})
    record["pages_crawled"] = pages_crawled
    record["total_pages"] = total
