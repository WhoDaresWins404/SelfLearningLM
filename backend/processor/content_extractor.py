from bs4 import BeautifulSoup
from bs4.element import Tag


def extract_content(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    for tag in soup.find_all(class_=lambda c: c and any(x in (c or "").lower() for x in ["nav", "sidebar", "menu", "footer", "header", "advert", "banner"])):
        tag.decompose()

    title = ""
    if soup.h1:
        title = soup.h1.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)

    main = soup.find("main") or soup.find("article") or soup.find(class_=lambda c: c and "content" in (c or "").lower())
    if not main:
        main = soup.find("body") or soup

    sections = []
    code_blocks = []
    current_section = {"heading": "", "paragraphs": []}

    for el in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "code", "li", "blockquote", "table"]):
        if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if current_section["paragraphs"]:
                sections.append(current_section)
            current_section = {"heading": el.get_text(strip=True), "paragraphs": []}
        elif el.name == "pre":
            code_tag = el.find("code") or el
            code_text = code_tag.get_text("\n", strip=True)
            if code_text:
                code_blocks.append(code_text)
                current_section["paragraphs"].append(f"```\n{code_text}\n```")
        elif el.name == "code":
            code_text = el.get_text(strip=True)
            if code_text:
                code_blocks.append(code_text)
        elif el.name == "table":
            rows = []
            for tr in el.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                current_section["paragraphs"].append("\n".join(rows))
        elif el.name == "blockquote":
            text = el.get_text(strip=True)
            if text:
                current_section["paragraphs"].append(f"> {text}")
        else:
            text = el.get_text(strip=True)
            if text and len(text) > 10:
                current_section["paragraphs"].append(text)

    if current_section["paragraphs"]:
        sections.append(current_section)

    clean_text = "\n\n".join(
        f"## {s['heading']}\n" + "\n".join(s["paragraphs"]) if s["heading"] else "\n".join(s["paragraphs"])
        for s in sections
    )

    return {
        "title": title,
        "clean_text": clean_text,
        "sections": sections,
        "code_blocks": code_blocks,
        "word_count": len(clean_text.split()),
        "has_code": len(code_blocks) > 0,
    }
