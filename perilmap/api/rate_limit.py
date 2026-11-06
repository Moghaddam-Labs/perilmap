"""Stop one visitor or a flood of bots from running up a bill.

This lives in memory, which suits the single server the app is set up to run on. Addresses
are scrambled with a key that's created at startup and never saved, and each is forgotten
once its minute has passed.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic

WINDOW_SECONDS = 60.0


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimiter:
    def __init__(
        self,
        client_limit: int,
        total_limit: int,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._client_limit = client_limit
        self._total_limit = total_limit
        self._clock = clock
        self._key = secrets.token_bytes(32)
        self._lock = threading.Lock()
        self._clients: dict[bytes, deque[float]] = {}
        self._total: deque[float] = deque()

    @property
    def tracked_clients(self) -> int:
        return len(self._clients)

    def _scramble(self, address: str) -> bytes:
        return hmac.new(self._key, address.encode(), hashlib.sha256).digest()

    def _forget_old(self, now: float) -> None:
        cutoff = now - WINDOW_SECONDS
        while self._total and self._total[0] <= cutoff:
            self._total.popleft()
        for client in list(self._clients):
            times = self._clients[client]
            while times and times[0] <= cutoff:
                times.popleft()
            if not times:
                del self._clients[client]

    def _wait(self, oldest: float, now: float) -> int:
        return max(1, int(oldest + WINDOW_SECONDS - now) + 1)

    def check(self, address: str) -> RateDecision:
        now = self._clock()
        client = self._scramble(address)
        with self._lock:
            self._forget_old(now)
            times = self._clients.get(client)
            if times and len(times) >= self._client_limit:
                return RateDecision(False, self._wait(times[0], now))
            if len(self._total) >= self._total_limit:
                return RateDecision(False, self._wait(self._total[0], now))
            self._clients.setdefault(client, deque()).append(now)
            self._total.append(now)
            return RateDecision(True)
