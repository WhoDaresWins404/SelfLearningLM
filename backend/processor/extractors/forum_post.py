from bs4 import BeautifulSoup


def extract_forum_post(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.h1 or soup.select_one(".post-title, .thread-title")
    author_tag = soup.select_one(".username, .author, .post-author")
    time_tag = soup.find("time") or soup.select_one(".date, .post-date")
    content_tag = soup.select_one(".post-content, .message, .post-body")
    code_tags = soup.find_all(["code", "pre"])

    return {
        "title": title_tag.get_text(strip=True) if title_tag else "",
        "author": author_tag.get_text(strip=True) if author_tag else "",
        "timestamp": (time_tag.get("datetime", "") or time_tag.get_text(strip=True)) if time_tag else "",
        "content": content_tag.get_text(strip=True) if content_tag else "",
        "code_snippets": [t.get_text(strip=True) for t in code_tags],
    }
