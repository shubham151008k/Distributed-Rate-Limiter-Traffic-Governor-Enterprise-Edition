"""Defaults and validation (PRD v0.3, Sections 7 and 10.1)."""
import re

DEFAULT_CAPACITY = 10
DEFAULT_REFILL_RATE = 2.0
DEFAULT_COST = 1

# Client keys: simulated labels / IPs typed or selected in the UI.
CLIENT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")

PRESET_CLIENTS = ["192.0.2.10", "198.51.100.7", "203.0.113.25"]


def validate_config(capacity, refill_rate, cost=DEFAULT_COST):
    """Check a new config. Returns (capacity, refill_rate, cost).

    Raises ValueError with a plain message if anything is invalid.
    Capacity: integer 1-1000. Refill rate: number > 0 and <= 1000/sec.
    Cost: integer >= 1 and <= capacity.
    """
    if capacity is None or refill_rate is None:
        raise ValueError("Capacity and refill rate are required.")
    try:
        capacity = int(capacity)
    except (TypeError, ValueError):
        raise ValueError("Capacity must be a whole number from 1 to 1000.")
    if isinstance(capacity, bool) or not 1 <= capacity <= 1000:
        raise ValueError("Capacity must be a whole number from 1 to 1000.")
    try:
        refill_rate = float(refill_rate)
    except (TypeError, ValueError):
        raise ValueError("Refill rate must be a number over 0 and up to 1000 per second.")
    if not 0 < refill_rate <= 1000:
        raise ValueError("Refill rate must be a number over 0 and up to 1000 per second.")
    try:
        cost = int(cost)
    except (TypeError, ValueError):
        raise ValueError("Cost must be a whole number.")
    if not 1 <= cost <= capacity:
        raise ValueError("Cost must be a whole number from 1 up to the capacity.")
    return capacity, refill_rate, cost


def validate_client_key(key):
    """Check a client key. Returns the key, or raises ValueError."""
    if not isinstance(key, str) or not CLIENT_KEY_PATTERN.match(key):
        raise ValueError(
            "Client must be 1-64 characters: letters, numbers, . _ : - only."
        )
    return key
