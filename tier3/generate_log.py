"""Tier 3: generate a synthetic traffic log (PRD v0.3, Section 6 / Journey E).

- 10,000 valid rows + 5 malformed rows (10,005 data lines total).
- Schema matches the Tier 2 CSV decision log so the analysis script can
  also accept a real Tier 2 log:
  timestamp,client_ip,decision,remaining_tokens,retry_after_ms,overhead_us
  decision is "allowed" or "rejected".
- IPs use the PRD documentation ranges only: 192.0.2.0/24,
  198.51.100.0/24, 203.0.113.0/24. No real user IPs.
- Seeded (random seed 42), so re-running gives the same log.

Run on Windows:
    python generate_log.py
    -> writes traffic_log.csv in this folder
"""
import csv
import random
from datetime import datetime, timedelta

SEED = 42
N_ROWS = 10_000
START = datetime(2026, 11, 5, 10, 0, 0)
WINDOW_SECONDS = 600  # 10 one-minute windows

# (ip, share of traffic, probability a request from this ip is rejected)
IPS = [
    ("203.0.113.10", 0.35, 0.45),   # heavy hitter, throttled most
    ("192.0.2.15", 0.20, 0.20),
    ("198.51.100.23", 0.15, 0.10),
    ("192.0.2.42", 0.10, 0.05),
    ("203.0.113.7", 0.08, 0.15),
    ("198.51.100.8", 0.06, 0.05),
    ("192.0.2.99", 0.04, 0.05),
    ("203.0.113.200", 0.02, 0.05),
]

MALFORMED_LINES = [
    "not-a-timestamp,203.0.113.10,allowed",
    "2026-11-05 10:00:00,203.0.113.10",
    "garbage line with no commas at all",
    "2026-13-99 25:61:61,192.0.2.15,rejected,0,500,100",
    ",,,",
]


def main():
    rng = random.Random(SEED)
    ips, weights, reject_rates = zip(*[(ip, w, r) for ip, w, r in IPS])
    reject_by_ip = dict(zip(ips, reject_rates))

    rows = []
    for _ in range(N_ROWS):
        ip = rng.choices(ips, weights=weights, k=1)[0]
        ts = START + timedelta(seconds=rng.randrange(WINDOW_SECONDS))
        rejected = rng.random() < reject_by_ip[ip]
        decision = "rejected" if rejected else "allowed"
        rows.append([
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            ip,
            decision,
            0 if rejected else rng.randint(0, 10),
            500 if rejected else 0,
            rng.randint(20, 200),
        ])
    rows.sort(key=lambda r: r[0])  # chronological, like a real log

    with open("traffic_log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "client_ip", "decision",
                         "remaining_tokens", "retry_after_ms", "overhead_us"])
        writer.writerows(rows)
        for line in MALFORMED_LINES:
            f.write(line + "\n")

    print(f"Wrote traffic_log.csv: {N_ROWS} valid rows + "
          f"{len(MALFORMED_LINES)} malformed lines")


if __name__ == "__main__":
    main()
