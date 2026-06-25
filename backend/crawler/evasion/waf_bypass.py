import random
import time

MIN_DELAY = 1.0
MAX_DELAY = 8.0
JITTER_FACTOR = 0.3


def jitter_delay(base_delay: float) -> float:
    jitter = base_delay * JITTER_FACTOR * random.uniform(-1, 1)
    return max(MIN_DELAY, base_delay + jitter)
