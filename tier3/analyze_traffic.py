"""Tier 3: traffic-log analysis (PRD v0.3, Section 6 / Journey E).

- pandas ingestion with timestamp parsing; malformed lines skipped + counted
- Top 5 IPs by request volume (ties broken by IP ascending)
- Allowed vs. rejected requests per 1-minute window
  (empty minutes shown as zero), plotted with matplotlib, saved as PNG
- Also accepts the Tier 2 CSV decision-log schema:
  timestamp,client_ip,decision,remaining_tokens,retry_after_ms,overhead_us

Run on Windows (after `pip install pandas matplotlib`, once):
    python generate_log.py
    python analyze_traffic.py
    -> prints the top 5 IPs and per-minute table
    -> writes allowed_vs_rejected_per_minute.png, top5_ips.csv,
       per_minute.csv in this folder

Usage: python analyze_traffic.py [log.csv]   (default: traffic_log.csv)
"""
import sys

import matplotlib
matplotlib.use("Agg")  # no window needed; just save the PNG
import matplotlib.pyplot as plt
import pandas as pd

LOG_FILE = sys.argv[1] if len(sys.argv) > 1 else "traffic_log.csv"


def main():
    with open(LOG_FILE, encoding="utf-8") as f:
        total_lines = sum(1 for _ in f) - 1  # minus the header row

    df = pd.read_csv(LOG_FILE, on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["decision"] = df["decision"].astype(str).str.strip().str.lower()
    parsed = df.dropna(subset=["timestamp", "client_ip"])
    parsed = parsed[parsed["decision"].isin(["allowed", "rejected"])]
    skipped = total_lines - len(parsed)

    print(f"Log: {LOG_FILE}")
    print(f"Total data lines: {total_lines}")
    print(f"Parsed rows: {len(parsed)}")
    print(f"Malformed lines skipped: {skipped}")
    print(f"Allowed: {(parsed['decision'] == 'allowed').sum()}  "
          f"Rejected: {(parsed['decision'] == 'rejected').sum()}")

    # Top 5 IPs by request volume; ties broken by IP ascending (PRD).
    top5 = (parsed.groupby("client_ip").size().reset_index(name="requests")
            .sort_values(["requests", "client_ip"],
                         ascending=[False, True]).head(5))
    print("\nTop 5 IPs by request volume:")
    print(top5.to_string(index=False))
    top5.to_csv("top5_ips.csv", index=False)

    # Allowed vs. rejected per 1-minute window; empty minutes shown as zero.
    parsed = parsed.copy()
    parsed["minute"] = parsed["timestamp"].dt.floor("min")
    per_minute = (parsed.groupby(["minute", "decision"]).size()
                  .unstack(fill_value=0))
    for col in ("allowed", "rejected"):
        if col not in per_minute.columns:
            per_minute[col] = 0
    full_range = pd.date_range(parsed["minute"].min(),
                               parsed["minute"].max(), freq="min")
    per_minute = per_minute.reindex(full_range, fill_value=0)
    per_minute.index.name = "minute"
    print("\nAllowed vs. rejected per minute:")
    print(per_minute[["allowed", "rejected"]].to_string())
    per_minute.to_csv("per_minute.csv")

    plt.figure(figsize=(10, 5))
    plt.plot(per_minute.index, per_minute["allowed"],
             marker="o", label="Allowed")
    plt.plot(per_minute.index, per_minute["rejected"],
             marker="o", label="Rejected")
    plt.xlabel("Minute")
    plt.ylabel("Requests")
    plt.title("Allowed vs. rejected requests per minute")
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("allowed_vs_rejected_per_minute.png", dpi=150)
    print("\nSaved: allowed_vs_rejected_per_minute.png, "
          "top5_ips.csv, per_minute.csv")


if __name__ == "__main__":
    main()
