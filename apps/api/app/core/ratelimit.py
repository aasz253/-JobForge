"""Lightweight in-memory rate limiting (per key + per route).

Sufficient for single-instance deployments. Distributed deployments should
swap this for a Redis-backed counter (interface unchanged).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock


@dataclass
class _Counter:
    window_start: float = 0.0
    hits: int = 0


class RateLimiter:
    def __init__(self) -> None:
        self._store: dict[str, _Counter] = defaultdict(_Counter)
        self._lock = Lock()
        self._history: dict[str, "deque[float]"] = defaultdict(deque)

    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            history = self._history[key]
            while history and history[0] <= now - window_seconds:
                history.popleft()
            if len(history) >= limit:
                return False
            history.append(now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._history.pop(key, None)


limiter = RateLimiter()