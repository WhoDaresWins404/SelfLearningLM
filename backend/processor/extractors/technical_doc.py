from bs4 import BeautifulSoup


def extract_detailed_technical_doc(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    return {
        "title": (soup.h1.get_text(strip=True) if soup.h1 else ""),
        "headings": [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])],
        "code_blocks": [
            tag.get_text(strip=True) for tag in soup.find_all(["code", "pre", "tt"])
        ],
        "parameters": [
            tag.get_text(strip=True) for tag in soup.select("param, .param, .parameter")
        ],
    }
