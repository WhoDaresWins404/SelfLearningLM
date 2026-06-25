import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class EvasionState:
    signal: str  # OK, RATE_LIMITED, CAPTCHA, BLOCKED, HONEYPOT
    consecutive_blocks: int = 0
    current_proxy_index: int = -1
    current_delay: float = 2.0
    fingerprint_rotation_count: int = 0


class EvasionStateMachine:
    def __init__(self, base_delay: float = 2.0):
        self.state = EvasionState(signal="OK", current_delay=base_delay)

    def transition(self, signal: str) -> dict:
        self.state.signal = signal

        if signal == "OK":
            self.state.consecutive_blocks = 0
            self.state.current_delay = max(1.0, self.state.current_delay * 0.8)
            return {"action": "continue", "delay": self.state.current_delay}

        if signal == "RATE_LIMITED":
            self.state.consecutive_blocks += 1
            self.state.current_delay = min(30.0, self.state.current_delay * 2.0)
            return {"action": "rotate_proxy", "delay": self.state.current_delay}

        if signal == "CAPTCHA":
            self.state.consecutive_blocks += 1
            self.state.current_delay = min(60.0, self.state.current_delay * 3.0)
            self.state.fingerprint_rotation_count += 1
            return {"action": "rotate_proxy_and_fingerprint", "delay": self.state.current_delay}

        if signal == "BLOCKED":
            self.state.consecutive_blocks += 1
            self.state.current_delay = min(120.0, self.state.current_delay * 4.0)
            self.state.fingerprint_rotation_count += 1
            if self.state.consecutive_blocks >= 3:
                return {"action": "dead_letter", "delay": self.state.current_delay}
            return {"action": "rotate_all", "delay": self.state.current_delay}

        if signal == "HONEYPOT":
            return {"action": "skip", "delay": self.state.current_delay}

        return {"action": "continue", "delay": self.state.current_delay}

    def reset(self):
        self.state = EvasionState(signal="OK", current_delay=2.0)
