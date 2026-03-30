"""Tests for rate limiter semantics."""

from __future__ import annotations

import pytest

from pykalshi.rate_limiter import AsyncRateLimiter, RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds + 1e-6

    async def async_sleep(self, seconds: float) -> None:
        self.sleep(seconds)


def test_rate_limiter_refills_at_configured_rate(monkeypatch):
    """The sync limiter should refill tokens at requests_per_second."""
    clock = FakeClock()
    monkeypatch.setattr("pykalshi.rate_limiter.time.monotonic", clock.monotonic)
    monkeypatch.setattr("pykalshi.rate_limiter.time.sleep", clock.sleep)

    limiter = RateLimiter(requests_per_second=2.0, burst=4)

    for _ in range(4):
        assert limiter.acquire() == 0.0

    clock.now += 1.0

    assert limiter.acquire() == 0.0
    assert limiter.acquire() == 0.0

    waited = limiter.acquire()
    assert waited == pytest.approx(0.5, rel=1e-3)
    assert clock.sleeps[-1] == pytest.approx(0.5, rel=1e-3)


@pytest.mark.asyncio
async def test_async_rate_limiter_refills_at_configured_rate(monkeypatch):
    """The async limiter should refill tokens at requests_per_second."""
    clock = FakeClock()
    monkeypatch.setattr("pykalshi.rate_limiter.time.monotonic", clock.monotonic)
    monkeypatch.setattr("pykalshi.rate_limiter.asyncio.sleep", clock.async_sleep)

    limiter = AsyncRateLimiter(requests_per_second=2.0, burst=4)

    for _ in range(4):
        assert await limiter.acquire() == 0.0

    clock.now += 1.0

    assert await limiter.acquire() == 0.0
    assert await limiter.acquire() == 0.0

    waited = await limiter.acquire()
    assert waited == pytest.approx(0.5, rel=1e-3)
    assert clock.sleeps[-1] == pytest.approx(0.5, rel=1e-3)
