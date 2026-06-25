import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STORAGE_ROOT = PROJECT_ROOT / "storage"
UNSTRUCTURED_DIR = STORAGE_ROOT / "unstructured" / "raw"
STRUCTURED_DIR = STORAGE_ROOT / "structured"
MAIN_DB_PATH = STRUCTURED_DIR / "selflearninglm.db"
LAKE_INDEX_DB_PATH = STRUCTURED_DIR / "lake_index.db"

PROXY_FILE = PROJECT_ROOT / "config" / "proxies.txt"
DEAD_LETTER_DIR = PROJECT_ROOT / "data" / "dead_letter"

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
DEFAULT_DOWNLOAD_DELAY = 2.0
MAX_RETRIES = 3
CONCURRENT_REQUESTS = 8

os.makedirs(UNSTRUCTURED_DIR, exist_ok=True)
os.makedirs(STRUCTURED_DIR, exist_ok=True)
os.makedirs(DEAD_LETTER_DIR, exist_ok=True)
