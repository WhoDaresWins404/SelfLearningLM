import re
import html


def clean_html_entities(text: str) -> str:
    return html.unescape(text)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_noise(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\b(javascript|function|var|let|const)\s*[;:{}\[\]()]?\b", "", text, flags=re.I)
    return text


def refine(extracted: dict) -> dict:
    result = {}
    for key, value in extracted.items():
        if isinstance(value, str):
            cleaned = clean_html_entities(value)
            cleaned = normalize_whitespace(cleaned)
            result[key] = cleaned
        elif isinstance(value, list):
            result[key] = [
                normalize_whitespace(clean_html_entities(str(item))) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result
