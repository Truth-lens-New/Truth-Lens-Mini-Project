"""
Tests for the sliding-window rate limiter (app/core/rate_limit.py).
"""

import pytest

from import_utils import isolated_imports


@pytest.fixture(scope="module")
def limiter_cls():
    with isolated_imports(["app", "app.core"]) as imp:
        yield imp("app.core.rate_limit").SlidingWindowLimiter


class TestSlidingWindow:
    def test_allows_up_to_limit(self, limiter_cls):
        lim = limiter_cls(max_events=3, window_seconds=60.0)
        assert lim.allow("user-1") is True
        assert lim.allow("user-1") is True
        assert lim.allow("user-1") is True
        assert lim.allow("user-1") is False

    def test_keys_are_independent(self, limiter_cls):
        lim = limiter_cls(max_events=1, window_seconds=60.0)
        assert lim.allow("user-1") is True
        assert lim.allow("user-2") is True
        assert lim.allow("user-1") is False

    def test_window_expiry_restores_quota(self, limiter_cls):
        lim = limiter_cls(max_events=1, window_seconds=10.0)
        assert lim.allow("user-1", now=1000.0) is True
        assert lim.allow("user-1", now=1005.0) is False
        assert lim.allow("user-1", now=1011.0) is True   # event from 1000 is out of window
        assert lim.allow("user-1", now=1016.0) is False

    def test_retry_after_is_positive(self, limiter_cls):
        lim = limiter_cls(max_events=1, window_seconds=10.0)
        lim.allow("user-1", now=1000.0)
        lim.allow("user-1", now=1002.0)                 # denied, not counted
        assert 1 <= lim.retry_after("user-1", now=1002.0) <= 10

    def test_zero_limit_denies_everything(self, limiter_cls):
        lim = limiter_cls(max_events=0)
        assert lim.allow("user-1") is False
