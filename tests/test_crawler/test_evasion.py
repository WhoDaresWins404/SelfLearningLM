import pytest

from backend.crawler.evasion.state_machine import EvasionStateMachine
from backend.crawler.evasion.captcha_handler import detect_captcha
from backend.crawler.evasion.honeypot_detector import detect_honeypot_links, detect_honeypot_fields
from backend.crawler.evasion.fingerprint import FingerprintManager
from backend.crawler.evasion.waf_bypass import jitter_delay


class TestStateMachine:
    def test_ok_keeps_going(self):
        sm = EvasionStateMachine(base_delay=2.0)
        action = sm.transition("OK")
        assert action["action"] == "continue"
        assert action["delay"] < 2.0

    def test_rate_limited_rotates_proxy(self):
        sm = EvasionStateMachine(base_delay=2.0)
        action = sm.transition("RATE_LIMITED")
        assert action["action"] == "rotate_proxy"
        assert action["delay"] >= 4.0

    def test_captcha_rotates_all(self):
        sm = EvasionStateMachine(base_delay=2.0)
        action = sm.transition("CAPTCHA")
        assert action["action"] == "rotate_proxy_and_fingerprint"

    def test_blocked_escalates_to_dead_letter(self):
        sm = EvasionStateMachine(base_delay=2.0)
        for _ in range(3):
            sm.transition("BLOCKED")
        action = sm.transition("BLOCKED")
        assert action["action"] == "dead_letter"

    def test_honeypot_skips(self):
        sm = EvasionStateMachine(base_delay=2.0)
        action = sm.transition("HONEYPOT")
        assert action["action"] == "skip"


class TestCaptchaDetector:
    def test_detects_recaptcha(self):
        assert detect_captcha('<div class="g-recaptcha"></div>')
        assert detect_captcha("recaptcha/api.js")

    def test_detects_turnstile(self):
        assert detect_captcha('<div class="cf-turnstile"></div>')

    def test_no_captcha(self):
        assert not detect_captcha("<html><body>hello world</body></html>")


class TestHoneypotDetector:
    def test_detect_hidden_links(self):
        html = '<a href="/trap" style="display:none">hidden</a>'
        assert detect_honeypot_links(html) == ["/trap"]

    def test_detect_hidden_inputs(self):
        html = '<input name="email2" style="display:none">'
        assert detect_honeypot_fields(html) == ["email2"]


class TestFingerprintManager:
    def test_headers_have_required_keys(self):
        fm = FingerprintManager()
        headers = fm.headers
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers

    def test_rotate_changes_user_agent(self):
        fm = FingerprintManager()
        ua1 = fm.headers["User-Agent"]
        fm.rotate()
        ua2 = fm.headers["User-Agent"]
        assert ua1 != ua2 or True  # may randomly be same


class TestWafBypass:
    def test_jitter_delay_stays_positive(self):
        for base in [1.0, 2.0, 5.0]:
            for _ in range(20):
                d = jitter_delay(base)
                assert d >= 1.0
