import re
import json

import trafilatura
from bs4 import BeautifulSoup

from backend.processor.cleanup import clean_content, clean_sections

# Minimum lines/characters for a code block to be considered "real" code
_MIN_CODE_LINES = 3
_MIN_CODE_CHARS = 40

# Boilerplate patterns (case-insensitive)
_BOILERPLATE_PATTERNS = [
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
]


def _clean_boilerplate(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        skip = False
        for pat in _BOILERPLATE_PATTERNS:
            if re.search(pat, stripped, re.IGNORECASE):
                skip = True
                break
        if not skip:
            cleaned.append(line)
    return "\n".join(cleaned)


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


def _merge_adjacent_code_blocks(blocks: list[dict]) -> list[dict]:
    if not blocks:
        return blocks
    merged = [blocks[0]]
    for b in blocks[1:]:
        last = merged[-1]
        if b["type"] == last["type"] == "code":
            if b.get("gap", 99) <= 1:
                last["text"] += "\n" + b["text"]
                last["lines"] = last["text"].count("\n") + 1
                continue
        merged.append(b)
    return merged


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


def _build_clean_text(sections: list[dict]) -> str:
    parts = []
    for s in sections:
        heading = s.get("heading", "")
        paras = s.get("paragraphs", [])
        if heading:
            parts.append(f"## {heading}")
        for p in paras:
            parts.append(p)
    return "\n\n".join(parts)


def _fix_inline_code_spacing(text: str) -> str:
    text = re.sub(r"(\S)(```)", r"\1 \2", text)
    text = re.sub(r"(```)(\S)", r"\1 \2", text)
    text = re.sub(r"([a-zA-Z0-9)])([\[({])", r"\1 \2", text)
    text = re.sub(r"([\]})])([a-zA-Z0-9(])", r"\1 \2", text)
    return text


def extract_content(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    title = _extract_title(soup)
    code_blocks = _extract_code_blocks(html)

    clean_text = ""
    xml_output = ""
    try:
        result = trafilatura.extract(html, output_format="txt", include_links=False, include_images=False, include_tables=True, no_fallback=False)
        if result and len(result.strip()) > 100:
            clean_text = result.strip()
        xml_result = trafilatura.extract(html, output_format="xml", include_links=False, include_images=False, include_tables=True, no_fallback=False)
        if xml_result:
            xml_output = xml_result
    except Exception:
        pass

    if clean_text:
        sections = _extract_sections_from_trafilatura_xml(xml_output) if xml_output else _extract_sections_from_html(html)
        clean_text = _clean_boilerplate(clean_text)
    else:
        clean_text = soup.get_text("\n", strip=True)
        sections = _extract_sections_from_html(html)

    clean_text = _fix_inline_code_spacing(clean_text)
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
