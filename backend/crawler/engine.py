from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

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

    process = CrawlerProcess(settings=spider_settings)
    process.crawl(GenericSpider, domain=domain, start_urls=start_urls, max_pages=max_pages)
    process.start()
