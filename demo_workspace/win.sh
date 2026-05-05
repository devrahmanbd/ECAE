#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Running install.ps1 ==="
pwsh -File "${SCRIPT_DIR}/install.ps1" \
  || { echo "install.ps1 failed, exiting"; exit 1; }

echo "Sleeping 10s..."
sleep 10

for i in {1..10}; do
  LOG="${SCRIPT_DIR}/tab${i}.log"
  echo "=== Launching tab${i}.ps1 → $(basename "$LOG") ==="
  nohup pwsh -File "${SCRIPT_DIR}/tab${i}.ps1" \
    > "$LOG" 2>&1 < /dev/null &
  echo "    PID $!  (you can `tail -f $LOG` to follow output)"
  sleep 5
done

echo "All scripts launched."