# Tier 3 — Traffic Analysis (PRD v0.3, required for full completion)

Tier 3 does **not** depend on Tier 2. It uses pandas + matplotlib only —
no Redis, no database, no FastAPI/Flask. The log is synthetic, with
documentation-range IPs only (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24).

## Files in this folder

- `generate_log.py` — seeded generator (seed 42): 10,000 valid rows + 5
  malformed lines, over 10 one-minute windows (10:00–10:09, 5 Nov 2026).
- `traffic_log.csv` — the generated log (10,005 data lines + header).
- `analyze_traffic.py` — pandas analysis + matplotlib chart.
- `allowed_vs_rejected_per_minute.png` — the chart.
- `top5_ips.csv`, `per_minute.csv` — the tables behind the chart.

## Run it (Windows, VS Code terminal)

```text
pip install pandas matplotlib
python generate_log.py
python analyze_traffic.py
```

Re-running gives the same log and the same numbers (seed 42).

## Verified result (run 5 Nov 2026)

- Total data lines: 10,005 — parsed 10,000, malformed skipped: 5
- Allowed: 7,605 — Rejected: 2,395 (23.9% rejected overall)
- Top 5 IPs by volume: 203.0.113.10 (3,478), 192.0.2.15 (1,987),
  198.51.100.23 (1,485), 192.0.2.42 (1,023), 203.0.113.7 (841).
  Together the top 5 are 88.1% of all requests.
- Rejections are spread evenly across the 10 minutes (216–266 rejected
  per minute), not one single spike.

## Findings paragraph (paste into the project README)

> In a synthetic 10,000-request log over 10 minutes, 7,605 requests were
> allowed and 2,395 rejected (23.9%). One client, 203.0.113.10, sent
> 3,478 requests (34.8% of all traffic) and was rejected 46.8% of the
> time (1,626 of its requests), while the other top IPs were rejected
> only 5–19% of the time — so the limiter throttled the heavy hitter
> while letting normal clients through. Rejections stayed steady at
> 216–266 per minute across all 10 minutes, with no single-minute spike.
> Five malformed log lines were skipped and counted by the analysis.
