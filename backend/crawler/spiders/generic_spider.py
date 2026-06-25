import hashlib
from typing import Optional
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.http import Response

from backend.app.crawl_tracker import set_current_url, set_progress
from backend.crawler.evasion.honeypot_detector import detect_honeypot_links, detect_honeypot_fields
from backend.storage.lake import store_blob, blob_exists_by_url, blob_exists_by_content


class GenericSpider(scrapy.Spider):
    name = "generic"

    def __init__(self, domain: str, start_urls: list[str], max_pages: int = 100,
                 allowed_domains: Optional[list[str]] = None, crawl_session_id: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.domain = domain
        self.start_urls = start_urls or [f"https://{domain}"]
        self.max_pages = max_pages
        self.allowed_domains = allowed_domains or [domain]
        self.pages_crawled = 0
        self.crawl_session_id = crawl_session_id
        self.logger.warning("SPIDER INIT: crawl_session_id=%s max_pages=%s domain=%s start_urls=%s", crawl_session_id, max_pages, domain, self.start_urls)
        if crawl_session_id:
            set_progress(crawl_session_id, 0, max_pages)

    def start_requests(self):
        self.logger.warning("START_REQUESTS: start_urls=%s", self.start_urls)
        for url in self.start_urls:
            self.logger.warning("START_REQUESTS yielding: %s", url)
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response: Response, **kwargs):
        self.logger.warning("SPIDER PARSE: url=%s crawl_session_id=%s pages_crawled=%s", response.url, self.crawl_session_id, self.pages_crawled)
        if self.pages_crawled >= self.max_pages:
            return

        if self.crawl_session_id:
            set_current_url(self.crawl_session_id, response.url)

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
        if self.crawl_session_id:
            set_progress(self.crawl_session_id, self.pages_crawled, self.max_pages)

        for href in response.css("a::attr(href)").getall():
            url = urljoin(response.url, href)
            parsed = urlparse(url)
            if parsed.netloc and not any(parsed.netloc.endswith(d) for d in self.allowed_domains):
                continue
            if not blob_exists_by_url(url):
                yield scrapy.Request(url, callback=self.parse)
