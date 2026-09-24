#!/bin/bash
# Monitor for the Kalshi summer pull. Owned by the parent agent (survives).
# Usage: monitor_pull.sh <run_log>   e.g. monitor_pull.sh hidden_files/summer_pull_run2.log
# Exits with a VERDICT line when the pull FINISHES, STALLS, or after 150 min.
cd ~/workspace/kalshi-paper || exit 1
LOG="$1"
RAW="kalshi_api_data_summer/raw"
OUT="kalshi_api_data_summer"

last_size=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
last_count=$(ls "$RAW" 2>/dev/null | wc -l)
still=0

for i in $(seq 1 75); do  # 75 x 120s = 150 min cap
  sleep 120

  # FINISHED: all outputs + DONE marker
  if [ -f "$OUT/market_data.csv" ] && [ -f "$OUT/market_metadata.csv" ] \
     && [ -f "$OUT/collection_log.json" ] && grep -q "DONE:" "$LOG" 2>/dev/null; then
    echo "VERDICT: FINISHED"
    grep "DONE:" "$LOG" | tail -2
    echo "raw_files=$(ls "$RAW" | wc -l)"
    echo "data_rows=$(( $(wc -l < "$OUT/market_data.csv") - 1 ))"
    echo "tickers_meta=$(( $(wc -l < "$OUT/market_metadata.csv") - 1 ))"
    exit 0
  fi

  # crashed with traceback
  if grep -q "Traceback" "$LOG" 2>/dev/null; then
    echo "VERDICT: STALLED (python traceback)"
    tail -25 "$LOG"
    echo "last_event: $(grep '^== ' "$LOG" | tail -1)"
    exit 0
  fi

  # collector process gone but outputs incomplete
  if ! pgrep -f "[c]ollect_kalshi_summer[.]py" >/dev/null 2>&1; then
    echo "VERDICT: STALLED (collector process gone, outputs incomplete)"
    tail -25 "$LOG"
    echo "last_event: $(grep '^== ' "$LOG" | tail -1)"
    exit 0
  fi

  # progress check: log size or raw file count
  size=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
  count=$(ls "$RAW" 2>/dev/null | wc -l)
  if [ "$size" = "$last_size" ] && [ "$count" = "$last_count" ]; then
    still=$((still + 1))
  else
    still=0; last_size=$size; last_count=$count
  fi
  if [ "$still" -ge 5 ]; then  # 10 min with zero progress
    echo "VERDICT: STALLED (no log/raw progress for 10 min)"
    echo "raw_files=$count"
    tail -15 "$LOG"
    echo "last_event: $(grep '^== ' "$LOG" | tail -1)"
    exit 0
  fi
done

echo "VERDICT: PROGRESSING (150 min elapsed, still moving)"
echo "raw_files=$(ls "$RAW" | wc -l)"
tail -3 "$LOG"
