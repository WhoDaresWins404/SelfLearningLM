import re
import base64
from bs4 import BeautifulSoup


_BASE64_RE = re.compile(r"base64\s*\(?\s*[\"']([A-Za-z0-9+/=]+)[\"']\s*\)?", re.I)


def try_decode_base64(s: str) -> str:
    try:
        decoded = base64.b64decode(s).decode("utf-8", errors="replace")
        return decoded
    except Exception:
        return ""


def extract_hidden_data(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    encoded_data = []

    for style in soup.find_all("style"):
        text = style.get_text()
        if text.strip():
            encoded_data.append(text.strip())

    for tag in soup.find_all(style=True):
        style_val = tag.get("style", "")
        if style_val.strip():
            encoded_data.append(style_val.strip())

    raw = "\n".join(encoded_data)
    decoded = ""
    technique = ""

    base64_match = _BASE64_RE.search(raw)
    if base64_match:
        decoded = try_decode_base64(base64_match.group(1))
        technique = "base64"

    if not decoded and re.search(r"@keyframes|animation-name", raw):
        technique = "css-keyframes"

    if not technique:
        technique = "css-style"

    return {
        "encoded_data": raw[:2000],
        "decoded_data": decoded[:2000],
        "technique": technique,
        "selector": "",
    }
