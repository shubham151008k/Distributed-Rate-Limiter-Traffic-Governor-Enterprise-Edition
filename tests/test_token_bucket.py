"""Unit tests (PRD v0.3, Tier 1, US-07).

Run:  python -m unittest
Uses a fake clock, so refill and the burst bound are exact,
not dependent on real time.
"""
import math
import unittest

from limiter.config import validate_client_key, validate_config
from limiter.store import BucketStore
from limiter.token_bucket import TokenBucket


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TestTokenBucket(unittest.TestCase):
    def test_starts_full_and_one_request_costs_one(self):
        bucket = TokenBucket(10, 2.0, clock=FakeClock())
        self.assertTrue(bucket.consume())
        self.assertEqual(bucket.tokens, 9)

    def test_burst_15_gives_10_allowed_5_denied(self):
        # PRD US-01: defaults, fresh client, 15 requests within 100 ms.
        clock = FakeClock()
        bucket = TokenBucket(10, 2.0, clock=clock)
        results = [bucket.consume() for _ in range(15)]
        self.assertEqual(sum(results), 10)
        self.assertEqual(results.count(False), 5)

    def test_refill_is_lazy_and_capped_at_capacity(self):
        clock = FakeClock()
        bucket = TokenBucket(10, 2.0, clock=clock)
        for _ in range(10):
            bucket.consume()
        self.assertEqual(bucket.tokens, 0)
        clock.advance(2)  # 2 seconds x 2 tokens/second = 4 tokens
        self.assertEqual(bucket.remaining(), 4)
        clock.advance(100)  # would refill far past capacity
        self.assertEqual(bucket.remaining(), 10)

    def test_backwards_clock_cannot_remove_tokens(self):
        clock = FakeClock()
        bucket = TokenBucket(10, 2.0, clock=clock)
        bucket.consume()
        clock.now -= 50  # clock goes backwards
        self.assertEqual(bucket.remaining(), 9)

    def test_denied_request_gives_retry_after(self):
        clock = FakeClock()
        bucket = TokenBucket(10, 2.0, clock=clock)
        for _ in range(10):
            bucket.consume()
        self.assertFalse(bucket.consume())
        # 1 token missing, refill 2/second -> 500 ms to wait.
        self.assertEqual(bucket.retry_after_ms(), 500)

    def test_allowed_never_exceeds_capacity_plus_refill_bound(self):
        # PRD Section 10.3: max allowed over Dt = floor(capacity + refill x Dt)
        clock = FakeClock()
        bucket = TokenBucket(10, 2.0, clock=clock)
        allowed = 0
        for _ in range(100):
            if bucket.consume():
                allowed += 1
            clock.advance(0.1)
        # First decision at t=0, last at t=9.9, so Dt = 9.9 seconds.
        expected = math.floor(10 + 2.0 * 9.9)  # = 29
        self.assertLessEqual(allowed, expected)
        self.assertEqual(allowed, expected)


class TestStoreAndConfig(unittest.TestCase):
    def test_client_isolation(self):
        # PRD US-03: after client A is denied, client B is still allowed.
        store = BucketStore()
        for _ in range(15):
            store.allow("192.0.2.10")
        self.assertTrue(store.allow("198.51.100.7")["allowed"])

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            validate_config(0, 2.0)
        with self.assertRaises(ValueError):
            validate_config(1001, 2.0)
        with self.assertRaises(ValueError):
            validate_config("ten", 2.0)
        with self.assertRaises(ValueError):
            validate_config(10, 0)
        with self.assertRaises(ValueError):
            validate_config(10, 1001)
        self.assertEqual(validate_config(10, 2.0), (10, 2.0, 1))

    def test_client_key_validation(self):
        self.assertEqual(validate_client_key("192.0.2.10"), "192.0.2.10")
        with self.assertRaises(ValueError):
            validate_client_key("bad client!")
        with self.assertRaises(ValueError):
            validate_client_key("x" * 65)

    def test_new_config_resets_buckets(self):
        store = BucketStore()
        for _ in range(10):
            store.allow("192.0.2.10")
        store.set_config(5, 1.0)
        result = store.allow("192.0.2.10")
        self.assertTrue(result["allowed"])
        self.assertEqual(result["remaining_tokens"], 4)


if __name__ == "__main__":
    unittest.main()
