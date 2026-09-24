#!/usr/bin/env python3
"""Build combined pair registry + combined market data for v2 extended runs.

- pairs_combined.csv: summer pairs + extended pairs (batches A-D).
  exploratory=1 for batch D (post-prereg window extension), 0 otherwise.
  Drops the 2 kawhi_to_raptors_xd KXCPI-26SEP post-only contracts.
- pairs_combined_supp.csv: same but exploratory=0 everywhere (supplementary run).
- market_data_combined.csv: summer + extended, deduped by (timestamp, ticker).
"""
import csv, json, os

PAPER = "/home/hatch/workspace/kalshi-paper"
HID = os.path.join(PAPER, "hidden_files")

SPORTS = ("KXNBA", "KXSB", "KXMLB")
SUPP_EVENTS = {  # batch D: post-prereg window extension
    "fomc_2026_01_supp", "fomc_2026_03_supp", "fomc_2026_04_supp",
    "fomc_2026_06_supp", "fomc_2026_07_supp",
    "cpi_2026_01_supp", "cpi_2026_02_supp", "cpi_2026_03_supp",
    "cpi_2026_04_supp", "cpi_2026_05_supp", "cpi_2026_06_supp",
    "cpi_2026_07_supp", "cpi_2026_08_supp",
}
DROP = {("kawhi_to_raptors_xd", "KXCPI-26SEP-T0.9"),
        ("kawhi_to_raptors_xd", "KXCPI-26SEP-T0.8")}

def market_kind(ticker):
    pfx = ticker.split("-")[0]
    return "sports_future" if pfx in SPORTS else "macro_bucket"

# --- summer pairs (as-is) ---
summer = list(csv.DictReader(open(os.path.join(HID, "analysis_registry_pairs.csv"))))
print("summer pairs:", len(summer))

# --- extended pairs ---
log = json.load(open(os.path.join(PAPER, "kalshi_api_data_extended/collection_log.json")))
ext = []
for e in log["events"]:
    eid, t0, cell = e["event_id"], e["t0_utc"], e["cell"]
    exp = 1 if eid in SUPP_EVENTS else 0
    for t in e["tickers"]:
        if (eid, t) in DROP:
            continue
        ext.append({
            "event_id": eid, "event_time": t0, "event_type": cell,
            "market_ticker": t, "market_kind": market_kind(t),
            "surprise": "", "moneyness_steps": "",
            "first_report_time": t0, "exploratory": exp,
        })
print("extended pairs:", len(ext), "| dropped:", len(DROP))

combined = summer + ext
with open(os.path.join(HID, "pairs_combined.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(combined[0].keys()))
    w.writeheader(); w.writerows(combined)

supp = [dict(r, exploratory=0) for r in combined]
with open(os.path.join(HID, "pairs_combined_supp.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(supp[0].keys()))
    w.writeheader(); w.writerows(supp)
print("wrote pairs_combined.csv (%d) and pairs_combined_supp.csv" % len(combined))

# --- combined market data ---
seen = set()
out = []
for path in [os.path.join(PAPER, "kalshi_api_data_summer/market_data.csv"),
             os.path.join(PAPER, "kalshi_api_data_extended/market_data.csv")]:
    for r in csv.DictReader(open(path)):
        k = (r["timestamp"], r["ticker"])
        if k not in seen:
            seen.add(k); out.append(r)
out.sort(key=lambda r: (r["ticker"], r["timestamp"]))
with open(os.path.join(HID, "market_data_combined.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["timestamp", "ticker", "bid", "ask",
                                      "last", "volume", "trades", "open_interest"])
    w.writeheader(); w.writerows(out)
print("wrote market_data_combined.csv (%d rows)" % len(out))
# sanity: no price-less rows
bad = [r for r in out if not r["bid"] and not r["ask"] and not r["last"]]
print("price-less rows in combined:", len(bad))
