#!/usr/bin/env python3
"""D24 pull: extend the analysis cutoff from 2026-09-21 to 2026-11-24.

The preregistration (section 4) defines scheduled macro as every FOMC/CPI
release "from 2026-08-14 through the analysis cutoff", and unscheduled sports
as every qualifying transaction "from 2026-06-01 -> cutoff". The cutoff was
never fixed, so these additions are within the locked protocol. Unscheduled
macro additions follow the same Tier-1 shock rule.

Reuses the collect_extended.py pipeline unchanged (same discovery, same daily
candles, same [T-45d, T+10d] windows); only EVENTS and the output folder
differ. Events whose T+10d window runs past "now" simply get the candles that
exist so far (headline 3-day window is complete for every event below).

Ex-ante size tiers for the new sports events were written to
hidden_files/size_tiers_d24.csv BEFORE this pull ran.
"""
import os
import collect_extended as ce

HERE = os.path.dirname(os.path.abspath(__file__))
ce.OUT_DIR = os.path.join(HERE, "kalshi_api_data_d24")
ce.RAW_DIR = os.path.join(ce.OUT_DIR, "raw")

TOP8 = {"select": "top_volume", "top_n": 8}

ce.EVENTS = [
    # ---- scheduled macro (prereg-mandated through cutoff) ----
    ("cpi_sep_release", "2026-10-14T12:30:00Z", "scheduled_macro",
     "scheduled_macro", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26SEP"}),
    ("fomc_oct_hold", "2026-10-28T18:00:00Z", "scheduled_macro",
     "scheduled_macro", ["KXFED"], {"ticker_contains": "26OCT"}),
    ("cpi_oct_release", "2026-11-10T13:30:00Z", "scheduled_macro",
     "scheduled_macro", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26OCT"}),
    # ---- scheduled sports (registered in Sept as "future, no data yet") ----
    ("nba_opening_night", "2026-10-20", "scheduled_sports",
     "scheduled_sports", ["KXNBA"], {}),
    ("nfl_trade_deadline", "2026-11-10T21:00:00Z", "scheduled_sports",
     "scheduled_sports", ["KXSB"], {}),
    # ---- unscheduled macro ----
    ("nvda_earnings_q3", "2026-11-17", "unscheduled_macro",
     "unscheduled_macro", ["KXFED", "KXCPI"], {}),
    ("hormuz_tanker_mines", "2026-11-18", "unscheduled_macro",
     "unscheduled_macro", ["KXCPI", "KXCPICORE", "KXFED"], {}),
    ("nvda_earnings_q3_xd", "2026-11-17", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], TOP8),
    ("hormuz_tanker_mines_xd", "2026-11-18", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], TOP8),
    # ---- unscheduled sports ----
    ("wemby_extension", "2026-07-10", "unscheduled_sports",
     "unscheduled_sports_extension", ["KXNBA"], {}),
    ("mccarthy_to_giants", "2026-09-28", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
    ("harrison_to_texans", "2026-10-10", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
    ("buckner_to_49ers", "2026-10-27", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
    ("simmons_to_bears", "2026-10-29", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
    ("jaguars_davis_bates", "2026-11-09", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
    ("cousins_to_vikings", "2026-11-10", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
    ("downs_to_chiefs", "2026-11-10", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
    ("allen_to_49ers", "2026-11-10", "unscheduled_sports",
     "unscheduled_sports_trade", ["KXSB"], {}),
]

if __name__ == "__main__":
    ce.main()
