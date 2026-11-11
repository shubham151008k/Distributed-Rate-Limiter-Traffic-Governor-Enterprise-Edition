"""Token bucket with lazy refill (PRD v0.3, Section 10.2).

Only the Python standard library is used. No Redis, no database,
no web framework.
"""
import math
import time


class TokenBucket:
    """One client's bucket.

    A bucket starts full. Tokens are added lazily, only when a
    request is checked, based on how much monotonic time has passed.
    """

    def __init__(self, capacity=10, refill_rate=2.0, cost=1, clock=None):
        self.capacity = int(capacity)
        self.refill_rate = float(refill_rate)
        self.cost = int(cost)
        # clock is injected for tests; in real use it is time.monotonic.
        # A fake clock in the tests lets us control time exactly.
        self._clock = clock or time.monotonic
        self.tokens = float(self.capacity)
        self.last_refill = self._clock()

    def _refill(self):
        now = self._clock()
        # max(0, ...) means a clock going backwards cannot remove tokens.
        elapsed = max(0.0, now - self.last_refill)
        self.tokens = min(
            float(self.capacity), self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

    def remaining(self):
        self._refill()
        return self.tokens

    def retry_after_ms(self, cost=None):
        """How long to wait before one request of this cost would pass."""
        cost = self.cost if cost is None else int(cost)
        self._refill()
        if self.tokens >= cost:
            return 0
        return math.ceil((cost - self.tokens) / self.refill_rate * 1000)

    def consume(self, cost=None):
        """Try to spend `cost` tokens. True = allowed, False = denied."""
        cost = self.cost if cost is None else int(cost)
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
