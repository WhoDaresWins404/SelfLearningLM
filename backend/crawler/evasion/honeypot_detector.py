from bs4 import BeautifulSoup

HONEYPOT_CSS_PATTERNS = [
    "display:none",
    "visibility:hidden",
    "opacity:0",
    "position:absolute",  # often off-screen
    "left:-9999px",
    "z-index:-1",
]


def detect_honeypot_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    suspicious = []

    for a in soup.find_all("a", href=True):
        style = a.get("style", "").replace(" ", "").lower()
        for pattern in HONEYPOT_CSS_PATTERNS:
            if pattern in style:
                suspicious.append(a["href"])
                break

        if a.get("hidden") is not None:
            suspicious.append(a["href"])

    return suspicious


def detect_honeypot_fields(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    suspicious = []

    for inp in soup.find_all("input"):
        style = inp.get("style", "").replace(" ", "").lower()
        for pattern in HONEYPOT_CSS_PATTERNS:
            if pattern in style:
                name = inp.get("name", "")
                if name:
                    suspicious.append(name)
                break

    return suspicious
