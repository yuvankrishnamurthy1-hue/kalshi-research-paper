#!/bin/bash
# Cron watchdog for the Kalshi summer pull. Runs every 20 min via cron.
# - FINISHED    -> prints verdict + coverage stats (cron worker reports it)
# - STALLED     -> kills any stale collector, starts a NEW DETACHED run
# - PROGRESSING -> prints progress
# Collector runs are launched DETACHED (setsid+nohup) so they survive
# whatever reaps tracked background sessions.
export PATH=/usr/local/bin:/usr/bin:/bin
cd /home/hatch/workspace/kalshi-paper || exit 1
HD="hidden_files"
OUT="kalshi_api_data_summer"
RAW="$OUT/raw"

latest_log() { ls -t $HD/summer_pull_run*.log 2>/dev/null | head -1; }
next_run_num() {
  ls $HD/summer_pull_run*.log 2>/dev/null \
    | sed 's/.*run\([0-9]*\)\.log/\1/' | sort -n | tail -1 | awk '{print $1+1}'
}
collector_alive() { pgrep -f "[c]ollect_kalshi_summer[.]py" >/dev/null 2>&1; }

LOG=$(latest_log)
[ -z "$LOG" ] && { echo "WATCHDOG: no runs yet"; exit 0; }

if [ -f "$OUT/market_data.csv" ] && [ -f "$OUT/market_metadata.csv" ] \
   && [ -f "$OUT/collection_log.json" ] && grep -q "DONE:" "$LOG" 2>/dev/null; then
  echo "WATCHDOG: FINISHED"
  grep "DONE:" "$LOG" | tail -1
  echo "raw_files=$(ls "$RAW" | wc -l)"
  echo "data_rows=$(( $(wc -l < "$OUT/market_data.csv") - 1 ))"
  exit 0
fi

if collector_alive; then
  if [ -n "$(find "$LOG" -mmin -20 2>/dev/null)" ]; then
    echo "WATCHDOG: PROGRESSING ($(basename "$LOG"), raw_files=$(ls "$RAW" | wc -l))"
    tail -2 "$LOG"
    exit 0
  fi
  echo "WATCHDOG: STALLED (process alive, log stale >20min) - killing and restarting"
  pkill -f "[c]ollect_kalshi_summer[.]py"
  sleep 2
else
  echo "WATCHDOG: STALLED (collector dead, outputs incomplete) - restarting"
fi

N=$(next_run_num)
[ -z "$N" ] && N=5
NEWLOG="$HD/summer_pull_run$N.log"
setsid nohup python3 /home/hatch/workspace/kalshi-paper/collect_kalshi_summer.py \
  > "$NEWLOG" 2>&1 < /dev/null &
echo "started run$N pid=$! log=$NEWLOG"
echo "$NEWLOG" > "$HD/current_run.txt"
echo "--- previous log tail ---"
tail -3 "$LOG"
