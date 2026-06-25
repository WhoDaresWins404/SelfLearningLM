import hashlib
from typing import Optional
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import Response

from backend.crawler.evasion.honeypot_detector import detect_honeypot_links, detect_honeypot_fields
from backend.storage.lake import store_blob, blob_exists_by_url, blob_exists_by_content


class GenericSpider(scrapy.Spider):
    name = "generic"

    def __init__(self, domain: str, start_urls: list[str], max_pages: int = 100,
                 allowed_domains: Optional[list[str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.domain = domain
        self.start_urls = start_urls or [f"https://{domain}"]
        self.max_pages = max_pages
        self.allowed_domains = allowed_domains or [domain]
        self.pages_crawled = 0

    def parse(self, response: Response, **kwargs):
        if self.pages_crawled >= self.max_pages:
            return

        body = response.text

        honeypot_links = detect_honeypot_links(body)
        honeypot_fields = detect_honeypot_fields(body)

        if honeypot_links or honeypot_fields:
            self.logger.warning(f"Honeypot detected on {response.url} — links={honeypot_links}, fields={honeypot_fields}")
            return

        if blob_exists_by_content(body):
            self.logger.debug(f"Skipping duplicate content at {response.url}")
            return

        store_blob(
            original_url=response.url,
            domain=self.domain,
            html_content=body,
            http_status=response.status,
            headers=dict(response.headers),
        )
        self.pages_crawled += 1

        for href in response.css("a::attr(href)").getall():
            url = urljoin(response.url, href)
            parsed = urlparse(url)
            if parsed.netloc and not any(parsed.netloc.endswith(d) for d in self.allowed_domains):
                continue
            if not blob_exists_by_url(url):
                yield scrapy.Request(url, callback=self.parse)
