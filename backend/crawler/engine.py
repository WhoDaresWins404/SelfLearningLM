import asyncio
import logging

from backend.app.config import settings

logger = logging.getLogger("crawl_engine")

# Install asyncio reactor BEFORE importing Scrapy (which would trigger epoll reactor)
_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_LOOP)
from twisted.internet import asyncioreactor  # noqa: E402
asyncioreactor.install(eventloop=_LOOP)

from twisted.internet import reactor  # noqa: E402 — returns the asyncio reactor we just installed
from twisted.python.failure import Failure  # noqa: E402
from scrapy.crawler import CrawlerRunner  # noqa: E402

from backend.crawler.spiders.generic_spider import GenericSpider  # noqa: E402


def run_spider(domain: str, start_urls: list[str], max_pages: int = 100, use_proxies: bool = False, crawl_session_id: int = 0):

    spider_settings = {
        "BOT_NAME": "selflearninglm",
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": settings.concurrent_requests,
        "DOWNLOAD_DELAY": settings.default_download_delay,
        "COOKIES_ENABLED": False,
        "TELNETCONSOLE_ENABLED": False,
        "LOG_LEVEL": "INFO",
        "DOWNLOADER_MIDDLEWARES": {
            "backend.crawler.middleware.EvasionMiddleware": 100,
        },
        "ITEM_PIPELINES": {
            "backend.crawler.pipelines.raw_storage.RawStoragePipeline": 300,
        },
    }

    runner = CrawlerRunner(settings=spider_settings)
    d = runner.crawl(GenericSpider, domain=domain, start_urls=start_urls, max_pages=max_pages, crawl_session_id=crawl_session_id)

    def _on_done(result):
        if isinstance(result, Failure):
            logger.error("Crawl FAILED:\n%s", result.getTraceback())
        else:
            logger.warning("Crawl finished successfully (result=%r)", result)
        reactor.stop()

    d.addBoth(_on_done)
    reactor.run(installSignalHandlers=False)
