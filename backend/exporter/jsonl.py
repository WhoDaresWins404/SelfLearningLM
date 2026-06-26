import json
from pathlib import Path


def export_jsonl(records: list[dict], config: dict) -> int:
    path_str = config.get("path", "exports/training_data.jsonl")
    file_path = Path(path_str)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    mode = config.get("mode", "append")
    count = 0
    with open(str(file_path), "a" if mode == "append" else "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1
    return count
