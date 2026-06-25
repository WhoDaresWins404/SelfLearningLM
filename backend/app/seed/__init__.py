import json

from backend.app.database import get_main_connection
from backend.app.seed.container_seeds import SEED_CONTAINERS


def seed_if_empty():
    conn = get_main_connection()
    count = conn.execute("SELECT COUNT(*) FROM containers").fetchone()[0]
    if count > 0:
        conn.close()
        return

    for c in SEED_CONTAINERS:
        conn.execute(
            "INSERT INTO containers (name, description, schema_def, extractors) VALUES (?, ?, ?, ?)",
            (c["name"], c["description"], json.dumps(c["schema_def"]), c["extractors"]),
        )
    conn.commit()
    conn.close()
