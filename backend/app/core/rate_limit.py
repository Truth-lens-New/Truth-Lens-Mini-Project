"""
Simple In-Memory Rate Limiter

Lightweight sliding-window limiter for expensive endpoints. Deliberately
single-process and memory-only: enough to blunt accidental/expensive abuse on a
small deployment without adding external dependencies (no Redis).
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional


class SlidingWindowLimiter:
    """Allow at most `max_events` calls per `window_seconds` per key."""

    def __init__(self, max_events: int, window_seconds: float = 60.0):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: Optional[float] = None) -> bool:
        """
        Record an event for `key` and report whether it is allowed.

        Returns False (and does NOT count the event) when the key has already
        reached its limit inside the current window.
        """
        if self.max_events <= 0:
            return False
        current = time.monotonic() if now is None else now
        window_start = current - self.window_seconds
        events = self._events[key]
        while events and events[0] <= window_start:
            events.popleft()
        if len(events) >= self.max_events:
            return False
        events.append(current)
        return True

    def retry_after(self, key: str, now: Optional[float] = None) -> int:
        """Seconds remaining until the key may retry (lower bound 1)."""
        current = time.monotonic() if now is None else now
        events = self._events.get(key)
        if not events:
            return 1
        oldest = events[0]
        remaining = self.window_seconds - (current - oldest)
        return max(1, int(remaining))
