import logging

from twisted.internet import reactor
from twisted.python.failure import Failure
from scrapy.crawler import CrawlerRunner

from backend.app.config import settings
from backend.crawler.spiders.generic_spider import GenericSpider

logger = logging.getLogger("crawl_engine")


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
    logger.warning("Starting reactor...")
    reactor.run(installSignalHandlers=False)
    logger.warning("Reactor stopped.")
