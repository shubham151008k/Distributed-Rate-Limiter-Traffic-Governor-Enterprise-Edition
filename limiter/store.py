"""Per-client bucket store (PRD v0.3, Sections 6 and 10.2).

One dictionary, keyed by client, protected by one threading.Lock.
The lock covers lookup AND update, so two threads cannot spend
the same token. New clients start with a full bucket.
State is in memory only and is lost on restart.
"""
import threading

from .config import (
    DEFAULT_CAPACITY,
    DEFAULT_COST,
    DEFAULT_REFILL_RATE,
    validate_client_key,
    validate_config,
)
from .token_bucket import TokenBucket


class BucketStore:
    def __init__(self, capacity=DEFAULT_CAPACITY,
                 refill_rate=DEFAULT_REFILL_RATE, cost=DEFAULT_COST,
                 clock=None):
        self.capacity, self.refill_rate, self.cost = validate_config(
            capacity, refill_rate, cost
        )
        self._clock = clock
        self._lock = threading.Lock()
        self._buckets = {}
        self.allowed_total = 0
        self.denied_total = 0

    def allow(self, client_key):
        """One decision for one client.

        Returns a dict with allowed (True/False) and remaining_tokens,
        exactly what the PRD demo and JSON endpoint need.
        """
        validate_client_key(client_key)
        with self._lock:
            bucket = self._buckets.get(client_key)
            if bucket is None:
                bucket = TokenBucket(
                    self.capacity, self.refill_rate, self.cost,
                    clock=self._clock,
                )
                self._buckets[client_key] = bucket
            allowed = bucket.consume()
            if allowed:
                self.allowed_total += 1
            else:
                self.denied_total += 1
            return {
                "client": client_key,
                "allowed": allowed,
                "remaining_tokens": bucket.tokens,
                "retry_after_ms": bucket.retry_after_ms(),
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
            }

    def status(self, client_key):
        validate_client_key(client_key)
        with self._lock:
            bucket = self._buckets.get(client_key)
            if bucket is None:
                return {
                    "client": client_key,
                    "remaining_tokens": float(self.capacity),
                    "capacity": self.capacity,
                    "refill_rate": self.refill_rate,
                }
            return {
                "client": client_key,
                "remaining_tokens": bucket.remaining(),
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
            }

    def set_config(self, capacity, refill_rate, cost=DEFAULT_COST):
        """Apply a valid new config. Existing buckets are reset (PRD US-02)."""
        capacity, refill_rate, cost = validate_config(capacity, refill_rate, cost)
        with self._lock:
            self.capacity, self.refill_rate, self.cost = capacity, refill_rate, cost
            self._buckets.clear()
            self.allowed_total = 0
            self.denied_total = 0

    def reset(self):
        with self._lock:
            self._buckets.clear()
            self.allowed_total = 0
            self.denied_total = 0

    def stats(self):
        with self._lock:
            return {
                "allowed": self.allowed_total,
                "denied": self.denied_total,
                "clients": len(self._buckets),
                "capacity": self.capacity,
                "refill_rate": self.refill_rate,
            }
