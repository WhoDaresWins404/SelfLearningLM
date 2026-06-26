import re
import json

import trafilatura
from bs4 import BeautifulSoup, Comment

from backend.processor.cleanup import clean_content, clean_sections, fix_sentence_boundaries

_MIN_CODE_LINES = 3
_MIN_CODE_CHARS = 40

_BOILERPLATE_LINE_PATTERNS = [
    r"◀\s*Back to the Blog",
    r"Back to the Blog",
    r"Written on\s+\w+ \d+,?\s*\d{4}",
    r"Posted\s+(?:on|at)\s+\w+\.?\s+\d+,?\s*\d{4}",
    r"Published\s+(?:on|at)\s+\w+\.?\s+\d+,?\s*\d{4}",
    r"Related posts? in this blog",
    r"Related\s+(?:posts?|articles?|content)",
    r"^\*+\s*Code\s*\*+$",
    r"^Code\s+(?:Blocks?|Examples?|Snippets?)\s*:?$",
    r"Tags:\s*.+",
    r"Categories?:\s*.+",
    r"Share this:?",
    r"Leave a (comment|reply)",
    r"\d+\s*(comments|replies)",
    r"Follow me on",
    r"Subscribe to",
    r"^\s*Tags?\s*$",
    r"^\s*Share\s*$",
    r"^\s*Comments?\s*$",
    r"^\s*Advertisement\s*$",
    r"^\s*Sponsored\s*$",
]

_NOISE_CLASS_PATTERNS = [
    "comment", "sidebar", "advert", "ad-", "social", "share", "related",
    "recommended", "widget", "newsletter", "subscribe", "popular",
    "trending", "footer", "cookie", "banner", "modal", "overlay",
    "breadcrumb", "pagination", "toc", "table.of.contents",
]

_HIDDEN_STYLE_PATTERNS = [
    r"display\s*:\s*none",
    r"visibility\s*:\s*hidden",
    r"opacity\s*:\s*0",
    r"position\s*:\s*absolute;\s*(left|top)\s*:\s*-\d+",
]


def _sanitize_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
        tag.decompose()

    for tag in soup.find_all(style=True):
        style = tag.get("style", "").lower()
        for pat in _HIDDEN_STYLE_PATTERNS:
            if re.search(pat, style):
                tag.decompose()
                break

    for tag in soup.find_all(True):
        classes = " ".join(tag.get("class", []))
        if classes:
            cls_lower = classes.lower()
            for noise in _NOISE_CLASS_PATTERNS:
                if noise in cls_lower:
                    tag.decompose()
                    break

    return str(soup)


def _extract_tables(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    tables = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                text = cell.get_text(strip=True)
                cells.append(text)
            if cells:
                rows.append(cells)
        if len(rows) >= 2:
            md_rows = []
            for i, row in enumerate(rows):
                md_rows.append("| " + " | ".join(row) + " |")
                if i == 0:
                    header_sep = "| " + " | ".join("---" for _ in row) + " |"
                    md_rows.append(header_sep)
            tables.append("\n".join(md_rows))
    return tables


def _clean_boilerplate(text: str, extra_patterns: list[str] | None = None) -> str:
    patterns = list(_BOILERPLATE_LINE_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)

    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        skip = False
        for pat in patterns:
            if re.search(pat, stripped, re.IGNORECASE):
                skip = True
                break
        if skip:
            i += 1
            continue
        block_end = i
        while block_end < len(lines) and lines[block_end].strip():
            block_end += 1
        block_lines = lines[i:block_end]
        block_text = "\n".join(bl for bl in block_lines if bl.strip())
        boilerplate_line_count = 0
        total_line_count = len(block_lines)
        for bl in block_lines:
            s = bl.strip()
            if not s or any(re.search(pat, s, re.IGNORECASE) for pat in patterns):
                boilerplate_line_count += 1
        if total_line_count > 2 and boilerplate_line_count > total_line_count * 0.6:
            i = block_end
            continue
        result.extend(block_lines)
        i = block_end
    return "\n".join(result)


def _is_raw_dump(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            json.loads(stripped)
            return True
        except (json.JSONDecodeError, ValueError):
            pass
    json_line_count = len(re.findall(r'^\s*["\[\{]', stripped, re.MULTILINE))
    if json_line_count > 10 and json_line_count > len(stripped.split("\n")) * 0.5:
        return True
    return False


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.h1:
        return soup.h1.get_text(strip=True)
    title_tag = soup.find("title")
    return title_tag.get_text(strip=True) if title_tag else ""


def _extract_code_blocks(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    blocks = []
    for tag in soup.find_all(["pre", "code"]):
        text = tag.get_text("\n")
        if text:
            blocks.append(text)
    seen = set()
    unique = []
    for cb in blocks:
        lines = [l for l in cb.split("\n") if l.strip()]
        if len(lines) < _MIN_CODE_LINES and len(cb.strip()) < _MIN_CODE_CHARS:
            continue
        h = hash(cb[:200])
        if h not in seen:
            seen.add(h)
            unique.append(cb)
    return unique


def _extract_sections_from_trafilatura_xml(xml_output: str) -> list[dict]:
    soup = BeautifulSoup(xml_output, "xml")
    sections = []
    current = {"heading": "", "paragraphs": [], "code_buffer": []}

    def _flush_code():
        if current["code_buffer"]:
            merged = "\n".join(current["code_buffer"])
            if merged.strip():
                current["paragraphs"].append(f"```\n{merged}\n```")
            current["code_buffer"] = []

    for el in soup.find_all(["head", "p", "code", "list", "quote"]):
        if el.name == "head":
            _flush_code()
            if current["paragraphs"]:
                sections.append(current)
            current = {"heading": "", "paragraphs": [], "code_buffer": []}
            current["heading"] = el.get_text(strip=True)
        elif el.name == "code":
            code_text = el.get_text("\n")
            code_text = "".join(c for c in code_text if c >= " " or c == "\n").strip()
            lines = [l for l in code_text.split("\n") if l.strip()]
            if len(lines) >= _MIN_CODE_LINES or len(code_text) >= _MIN_CODE_CHARS:
                current["code_buffer"].append(code_text)
            else:
                current["paragraphs"].append(code_text)
        elif el.name == "list":
            _flush_code()
            for item in el.find_all("item"):
                text = item.get_text(strip=True)
                if text:
                    current["paragraphs"].append(f"- {text}")
        elif el.name == "quote":
            _flush_code()
            text = el.get_text(strip=True)
            if text:
                current["paragraphs"].append(f"> {text}")
        else:
            _flush_code()
            text = el.get_text(strip=True)
            if text and len(text) > 10:
                current["paragraphs"].append(text)
    _flush_code()
    if current["paragraphs"]:
        sections.append(current)
    return sections


def _extract_sections_from_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    main = (soup.find("main") or soup.find("article") or
            soup.find(class_=lambda c: c and any(x in (c or "").lower() for x in ["content", "article", "post", "main"])) or
            soup.find("body") or soup)
    sections = []
    current = {"heading": "", "paragraphs": [], "code_buffer": []}

    def _flush_code():
        if current["code_buffer"]:
            merged = "\n".join(current["code_buffer"])
            if merged.strip():
                current["paragraphs"].append(f"```\n{merged}\n```")
            current["code_buffer"] = []

    for el in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "code", "li", "blockquote"]):
        if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            _flush_code()
            if current["paragraphs"]:
                sections.append(current)
            current = {"heading": "", "paragraphs": [], "code_buffer": []}
            current["heading"] = el.get_text(strip=True)
        elif el.name in ("pre", "code"):
            text = el.get_text("\n")
            text = "".join(c for c in text if c >= " " or c == "\n").strip()
            lines = [l for l in text.split("\n") if l.strip()]
            if el.name == "pre" or (len(lines) >= _MIN_CODE_LINES or len(text) >= _MIN_CODE_CHARS):
                current["code_buffer"].append(text)
            else:
                inline = el.get_text()
                current["paragraphs"].append(inline)
        elif el.name == "blockquote":
            _flush_code()
            text = el.get_text(strip=True)
            if text:
                current["paragraphs"].append(f"> {text}")
        else:
            _flush_code()
            text = el.get_text(strip=True)
            if text and len(text) > 10:
                current["paragraphs"].append(text)
    _flush_code()
    if current["paragraphs"]:
        sections.append(current)
    return sections


def extract_content(html: str, extra_boilerplate: list[str] | None = None) -> dict:
    sanitized = _sanitize_html(html)
    soup = BeautifulSoup(sanitized, "lxml")
    title = _extract_title(soup)

    code_blocks = _extract_code_blocks(sanitized)
    tables = _extract_tables(sanitized)

    clean_text = ""
    xml_output = ""
    try:
        result = trafilatura.extract(sanitized, output_format="txt", include_links=False, include_images=False, include_tables=True, no_fallback=False)
        if result and len(result.strip()) > 100:
            clean_text = result.strip()
        xml_result = trafilatura.extract(sanitized, output_format="xml", include_links=False, include_images=False, include_tables=True, no_fallback=False)
        if xml_result:
            xml_output = xml_result
    except Exception:
        pass

    if clean_text:
        sections = _extract_sections_from_trafilatura_xml(xml_output) if xml_output else _extract_sections_from_html(sanitized)
        clean_text = _clean_boilerplate(clean_text, extra_boilerplate)
    else:
        clean_text = soup.get_text("\n", strip=True)
        sections = _extract_sections_from_html(sanitized)

    if tables:
        clean_text += "\n\n" + "\n\n".join(tables)
        if sections:
            sections.append({"heading": "Tables", "paragraphs": tables})

    clean_text = fix_sentence_boundaries(clean_text)
    clean_text = clean_content(clean_text)
    sections = clean_sections(sections)

    is_dump = _is_raw_dump(clean_text) if clean_text else False

    return {
        "title": title,
        "clean_text": clean_text,
        "sections": sections,
        "code_blocks": code_blocks,
        "word_count": len(clean_text.split()),
        "has_code": len(code_blocks) > 0,
        "is_raw_dump": is_dump,
    }
