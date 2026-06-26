import re
from typing import Optional

from bs4 import BeautifulSoup


def analyze_blob(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    scores = {}

    has_pre_code = bool(soup.find_all(["pre", "code", "tt"]))
    has_article = bool(soup.find_all("article"))
    has_forum_structure = bool(soup.select(".post, .post-content, .message, .username, .forum"))
    has_script = bool(soup.find_all("script"))
    has_obfuscation = bool(
        soup.find_all(attrs={"data-malformed": True})
        or soup.find_all(class_=re.compile(r"(obfuscat|bad|malformed)", re.I))
        or bool(re.search(r"eval\(|String\.fromCharCode|base64", html, re.I))
    )
    has_style = bool(soup.find_all("style"))
    has_css_hidden = bool(
        re.search(r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0", html, re.I)
    )
    has_fetch = bool(re.search(r"fetch\(|XMLHttpRequest|axios\.", html))
    has_api_pattern = bool(re.search(r"/api/|/v1/|/v2/|\.json", html))
    has_iframe = bool(soup.find_all("iframe"))

    # Technical Documentation
    if has_pre_code and not has_forum_structure:
        base = sum([
            3 if has_pre_code else 0,
            2 if soup.find_all(["h1", "h2"]) else 0,
        ])
        scores["Detailed Technical Documentation"] = base / 5.0

    # Forum Posts
    if has_article or has_forum_structure:
        base = sum([
            3 if has_forum_structure else 0,
            2 if has_article else 0,
            1 if soup.find_all("time") else 0,
        ])
        scores["Forum Posts and Discussions"] = base / 6.0

    # Obfuscated Code
    if has_obfuscation or (has_script and has_style):
        base = sum([
            4 if has_obfuscation else 0,
            2 if has_script else 0,
        ])
        scores["Malformed or Obfuscated Code Snippets"] = base / 6.0

    # Dynamic Content
    if has_fetch or has_api_pattern or has_iframe:
        base = sum([
            3 if has_fetch else 0,
            2 if has_api_pattern else 0,
            1 if has_iframe else 0,
        ])
        scores["Dynamic Content (AJAX Calls)"] = base / 6.0

    # Hidden Data
    if has_css_hidden or (has_style and has_obfuscation):
        base = sum([
            3 if has_css_hidden else 0,
            2 if has_style else 0,
        ])
        scores["Hidden Data (CSS/JS Obfuscation)"] = base / 5.0

    threshold = 0.3
    return sorted(
        [name for name, score in scores.items() if score >= threshold],
        key=lambda n: scores[n], reverse=True,
    )
