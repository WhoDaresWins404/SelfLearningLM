from pathlib import Path

from backend.exporter.jsonl import export_jsonl

EXPORTERS = {
    "jsonl": export_jsonl,
}


def export_training(records: list[dict], target: dict) -> int:
    exporter = EXPORTERS.get(target["type"])
    if not exporter:
        return 0
    config = _parse_config(target["config"])
    return exporter(records, config)


def _parse_config(raw: str) -> dict:
    import json
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
