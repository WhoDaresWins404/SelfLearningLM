from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner

from backend.app.config import settings
from backend.crawler.spiders.generic_spider import GenericSpider


def run_spider(domain: str, start_urls: list[str], max_pages: int = 100, use_proxies: bool = False):
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
    d = runner.crawl(GenericSpider, domain=domain, start_urls=start_urls, max_pages=max_pages)
    d.addBoth(lambda _: reactor.stop())
    reactor.run(installSignalHandlers=False)
