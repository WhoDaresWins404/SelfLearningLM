import re
from bs4 import BeautifulSoup


def detect_technique(text: str) -> str:
    if "eval(" in text:
        return "eval"
    if "String.fromCharCode" in text:
        return "string-fromcharcode"
    if "base64" in text.lower() or re.search(r"btoa\(|atob\(", text):
        return "base64"
    if re.search(r"\\x[0-9a-fA-F]{2}", text):
        return "hex-encoding"
    if re.search(r"decodeURIComponent|unescape", text):
        return "uri-encoding"
    return "unknown"


def extract_obfuscated_code(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    scripts = [s.get_text(strip=True) for s in soup.find_all("script") if s.get_text(strip=True)]
    suspicious = soup.select("[data-malformed], .obfuscated, .bad")

    raw = scripts[0] if scripts else ""
    return {
        "raw_script": raw,
        "decoded_payload": "",
        "technique": detect_technique(raw),
        "suspicious_indicators": [s.get("class", []) for s in suspicious],
    }
