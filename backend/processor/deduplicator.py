import hashlib

from backend.storage.lake import blob_exists_by_url, blob_exists_by_content


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def is_duplicate(url: str, html: str) -> bool:
    return blob_exists_by_url(url) or blob_exists_by_content(html)
