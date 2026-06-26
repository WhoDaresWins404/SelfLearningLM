import trafilatura
from bs4 import BeautifulSoup


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.h1:
        return soup.h1.get_text(strip=True)
    title_tag = soup.find("title")
    return title_tag.get_text(strip=True) if title_tag else ""


def _extract_code_blocks(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    blocks = []
    for tag in soup.find_all(["pre", "code"]):
        text = tag.get_text("\n", strip=True)
        if text:
            blocks.append(text)
    seen = set()
    unique = []
    for cb in blocks:
        h = hash(cb[:200])
        if h not in seen:
            seen.add(h)
            unique.append(cb)
    return unique


def _extract_sections_from_trafilatura_xml(xml_output: str) -> list[dict]:
    soup = BeautifulSoup(xml_output, "xml")
    sections = []
    current = {"heading": "", "paragraphs": []}
    for el in soup.find_all(["head", "p", "code", "list", "quote"]):
        if el.name == "head":
            if current["paragraphs"]:
                sections.append(current)
            current = {"heading": el.get_text(strip=True), "paragraphs": []}
        elif el.name == "code":
            code_text = el.get_text("\n", strip=True)
            if code_text:
                current["paragraphs"].append(f"```\n{code_text}\n```")
        elif el.name == "list":
            for item in el.find_all("item"):
                text = item.get_text(strip=True)
                if text:
                    current["paragraphs"].append(f"- {text}")
        elif el.name == "quote":
            text = el.get_text(strip=True)
            if text:
                current["paragraphs"].append(f"> {text}")
        else:
            text = el.get_text(strip=True)
            if text and len(text) > 10:
                current["paragraphs"].append(text)
    if current["paragraphs"]:
        sections.append(current)
    return sections


def _extract_sections_from_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    main = (soup.find("main") or soup.find("article") or
            soup.find(class_=lambda c: c and any(x in (c or "").lower() for x in ["content", "article", "post", "main"])) or
            soup.find("body") or soup)
    sections = []
    current = {"heading": "", "paragraphs": []}
    for el in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "code", "li", "blockquote"]):
        if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if current["paragraphs"]:
                sections.append(current)
            current = {"heading": el.get_text(strip=True), "paragraphs": []}
        elif el.name in ("pre", "code"):
            text = el.get_text("\n", strip=True)
            if text:
                current["paragraphs"].append(f"```\n{text}\n```")
        elif el.name == "blockquote":
            text = el.get_text(strip=True)
            if text:
                current["paragraphs"].append(f"> {text}")
        else:
            text = el.get_text(strip=True)
            if text and len(text) > 10:
                current["paragraphs"].append(text)
    if current["paragraphs"]:
        sections.append(current)
    return sections


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
    else:
        clean_text = soup.get_text("\n", strip=True)
        sections = _extract_sections_from_html(html)

    return {
        "title": title,
        "clean_text": clean_text,
        "sections": sections,
        "code_blocks": code_blocks,
        "word_count": len(clean_text.split()),
        "has_code": len(code_blocks) > 0,
    }
