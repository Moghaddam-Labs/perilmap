from __future__ import annotations

from perilmap.api.rate_limit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


def test_one_client_is_limited_without_affecting_others() -> None:
    limiter = RateLimiter(2, 100, FakeClock())
    assert limiter.check("a").allowed and limiter.check("a").allowed
    assert not limiter.check("a").allowed
    assert limiter.check("b").allowed


def test_limit_clears_after_the_window() -> None:
    clock = FakeClock()
    limiter = RateLimiter(1, 100, clock)
    assert limiter.check("a").allowed
    clock.now += 30
    decision = limiter.check("a")
    assert not decision.allowed and decision.retry_after_seconds == 31
    clock.now += 31
    assert limiter.check("a").allowed


def test_total_limit_applies_across_all_clients() -> None:
    limiter = RateLimiter(100, 2, FakeClock())
    assert limiter.check("a").allowed and limiter.check("b").allowed
    assert not limiter.check("c").allowed


def test_refused_requests_do_not_use_up_the_total() -> None:
    limiter = RateLimiter(1, 3, FakeClock())
    assert limiter.check("a").allowed
    assert not limiter.check("a").allowed
    assert not limiter.check("a").allowed
    assert limiter.check("b").allowed and limiter.check("c").allowed


def test_addresses_are_scrambled_and_forgotten() -> None:
    clock = FakeClock()
    limiter = RateLimiter(5, 100, clock)
    limiter.check("203.0.113.9")
    assert b"203.0.113.9" not in b"".join(limiter._clients)
    assert limiter.tracked_clients == 1
    clock.now += 61
    limiter.check("198.51.100.1")
    assert limiter.tracked_clients == 1
