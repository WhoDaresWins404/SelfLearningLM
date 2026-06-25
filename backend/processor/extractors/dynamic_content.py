import re
from bs4 import BeautifulSoup


_FETCH_RE = re.compile(r'(fetch|axios|XMLHttpRequest)\s*\(\s*["\']([^"\']+)', re.I)


def extract_dynamic_content(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    scripts = [s.get_text() for s in soup.find_all("script") if s.get_text()]

    endpoints = []
    for script in scripts:
        for match in _FETCH_RE.finditer(script):
            endpoints.append(match.group(2))

    return {
        "endpoint": endpoints[0] if endpoints else "",
        "method": "",
        "payload": {},
        "trigger_event": "",
    }
