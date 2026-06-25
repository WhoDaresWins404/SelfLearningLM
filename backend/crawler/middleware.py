from scrapy import signals
from scrapy.http import Response

from backend.crawler.evasion.fingerprint import FingerprintManager
from backend.crawler.evasion.state_machine import EvasionStateMachine
from backend.crawler.evasion.proxy_rotator import ProxyRotator
from backend.crawler.evasion.captcha_handler import detect_captcha
from backend.crawler.evasion.honeypot_detector import detect_honeypot_links
from backend.crawler.evasion.waf_bypass import jitter_delay


class EvasionMiddleware:
    def __init__(self, crawler):
        self.fingerprint = FingerprintManager()
        self.state_machine = EvasionStateMachine(base_delay=crawler.settings.getfloat("DOWNLOAD_DELAY", 2.0))
        self.proxy_rotator = ProxyRotator(enabled=False)
        crawler.signals.connect(self._response_received, signal=signals.response_received)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        request.headers.update(self.fingerprint.headers)

        proxy = self.proxy_rotator.get_proxy()
        if proxy:
            request.meta["proxy"] = proxy

        delay = self.state_machine.state.current_delay
        request.meta["download_delay"] = jitter_delay(delay)
        return None

    def _classify_response(self, response: Response, spider) -> str:
        if response.status in (429, 503):
            return "RATE_LIMITED"
        if response.status in (403, 401, 407):
            return "BLOCKED"
        if response.status == 302 and "captcha" in response.headers.get("Location", "").lower():
            return "CAPTCHA"

        body = response.text.lower()
        if detect_captcha(body):
            return "CAPTCHA"

        honeypot = detect_honeypot_links(body)
        if honeypot:
            spider.logger.warning(f"Honeypot links detected: {honeypot}")
            return "HONEYPOT"

        return "OK"

    def _response_received(self, signal, response, request, spider, **kwargs):
        signal = self._classify_response(response, spider)
        action = self.state_machine.transition(signal)

        if action["action"] == "dead_letter":
            spider.crawler.stats.inc_value("evasion/dead_letter")
        elif action["action"] == "rotate_proxy":
            self.proxy_rotator = ProxyRotator(enabled=True)
        elif action["action"] in ("rotate_all", "rotate_proxy_and_fingerprint"):
            self.proxy_rotator = ProxyRotator(enabled=True)
            self.fingerprint.rotate()
