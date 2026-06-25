from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "SelfLearningLM"
    debug: bool = True

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    storage_root: Path = project_root / "storage"
    unstructured_dir: Path = storage_root / "unstructured" / "raw"
    structured_dir: Path = storage_root / "structured"
    data_dir: Path = project_root / "data"
    dead_letter_dir: Path = data_dir / "dead_letter"
    proxy_file: Path = project_root / "config" / "proxies.txt"

    # SQLite databases
    main_db_path: Path = structured_dir / "selflearninglm.db"
    lake_index_db_path: Path = structured_dir / "lake_index.db"

    # Frontend
    frontend_dist: Path = project_root / "frontend" / "dist"

    # Crawler defaults
    default_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    default_download_delay: float = 2.0
    max_retries: int = 3
    concurrent_requests: int = 8

    model_config = {"env_prefix": "SELFLM_", "env_file": ".env"}


settings = Settings()
