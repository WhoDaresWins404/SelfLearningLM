import re
from typing import Any


def score(extracted: dict) -> float:
    score = 50.0

    text_length = sum(len(str(v)) for v in extracted.values())
    if text_length > 500:
        score += 20
    elif text_length > 100:
        score += 10

    filled_fields = sum(1 for v in extracted.values() if v)
    total_fields = max(len(extracted), 1)
    score += (filled_fields / total_fields) * 20

    return min(100.0, round(score, 1))
