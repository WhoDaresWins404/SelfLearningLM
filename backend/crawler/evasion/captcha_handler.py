import re

CAPTCHA_PATTERNS = [
    re.compile(r"captcha", re.IGNORECASE),
    re.compile(r"recaptcha", re.IGNORECASE),
    re.compile(r"hcaptcha", re.IGNORECASE),
    re.compile(r"g-recaptcha", re.IGNORECASE),
    re.compile(r"cf-turnstile", re.IGNORECASE),
    re.compile(r"challenge-platform", re.IGNORECASE),
    re.compile(r"verify.*human", re.IGNORECASE),
]


def detect_captcha(html: str) -> bool:
    for pattern in CAPTCHA_PATTERNS:
        if pattern.search(html):
            return True
    return False
