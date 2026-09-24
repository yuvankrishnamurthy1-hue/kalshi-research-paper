#!/bin/bash
# Watchdog for the Kalshi summer pull. Exits with a verdict as soon as one is known.
LOG=~/workspace/kalshi-paper/hidden_files/summer_pull_run2.log
RAW=~/workspace/kalshi-paper/kalshi_api_data_summer/raw
OUT=~/workspace/kalshi-paper/kalshi_api_data_summer
prev_logsize=-1
prev_rawcount=-1
stall_count=0

for i in $(seq 1 75); do
  # FINISHED: all three outputs exist and log shows DONE
  if [ -f "$OUT/market_data.csv" ] && [ -f "$OUT/market_metadata.csv" ] \
     && [ -f "$OUT/collection_log.json" ] && grep -q "DONE:" "$LOG" 2>/dev/null; then
    echo "VERDICT=FINISHED"
    echo "timestamp=$(date '+%F %T %Z')"
    echo "raw_count=$(ls "$RAW" 2>/dev/null | wc -l)"
    echo "---coverage---"
    python3 - "$OUT/collection_log.json" <<'EOF'
import json, sys
log = json.load(open(sys.argv[1]))
print("tickers_in_log:", len(log.get("tickers", {})))
print("events:", len(log.get("events", [])))
print("event_ids:", ",".join(e["event_id"] for e in log.get("events", [])))
print("total_gaps:", sum(len(e.get("gaps", [])) for e in log.get("events", [])))
EOF
    echo "market_data_rows=$(($(wc -l < "$OUT/market_data.csv") - 1))"
    echo "metadata_rows=$(($(wc -l < "$OUT/market_metadata.csv") - 1))"
    echo "---log tail---"
    tail -5 "$LOG"
    exit 0
  fi
  # TRACEBACK: python died with an exception
  if grep -q "Traceback (most recent call last)" "$LOG" 2>/dev/null; then
    echo "VERDICT=STALLED_TRACEBACK"
    echo "timestamp=$(date '+%F %T %Z')"
    echo "raw_count=$(ls "$RAW" 2>/dev/null | wc -l)"
    echo "---last 30 log lines---"
    tail -30 "$LOG"
    exit 0
  fi
  logsize=$(stat -c%s "$LOG" 2>/dev/null || echo -1)
  rawcount=$(ls "$RAW" 2>/dev/null | wc -l)
  if [ "$logsize" = "$prev_logsize" ] && [ "$rawcount" = "$prev_rawcount" ]; then
    stall_count=$((stall_count + 1))
  else
    stall_count=0
  fi
  prev_logsize=$logsize
  prev_rawcount=$rawcount
  if [ "$stall_count" -ge 5 ]; then
    echo "VERDICT=STALLED_NOPROGRESS"
    echo "timestamp=$(date '+%F %T %Z')"
    echo "raw_count=$rawcount"
    echo "log_size=$logsize"
    echo "---last 30 log lines---"
    tail -30 "$LOG"
    echo "---most recent event/series markers---"
    grep "^== " "$LOG" 2>/dev/null | tail -3
    exit 0
  fi
  sleep 120
done

echo "VERDICT=PROGRESSING"
echo "timestamp=$(date '+%F %T %Z')"
echo "raw_count=$(ls "$RAW" 2>/dev/null | wc -l)"
echo "log_size=$(stat -c%s "$LOG" 2>/dev/null)"
tail -5 "$LOG"
