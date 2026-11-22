#!/usr/bin/env bash
set -u

KEY="webapp_data"
THRESHOLD=5
WINDOW_SEC=30
SIM_SOURCE_IP="192.0.2.77"

while true; do
  # Count SYSCALL events for webapp_data in the recent window
  COUNT=$(sudo ausearch -k "$KEY" --start recent 2>/dev/null | grep -c "type=SYSCALL" || true)
  EXE_LIST=$(sudo ausearch -k "$KEY" --start recent 2>/dev/null | awk -F'exe="' '/type=SYSCALL/ && $2 {split($2, a, "\""); print a[1]}' | sort | uniq -c | tr '\n' '; ')

  if [ "$COUNT" -gt "$THRESHOLD" ]; then
    echo "[$(date -Is)] ALERT: $COUNT read/access events on $KEY (executables: ${EXE_LIST:-none}) -> banning $SIM_SOURCE_IP via fail2ban"
    sudo fail2ban-client set sshd banip "$SIM_SOURCE_IP" 2>/dev/null || true
  else
    echo "[$(date -Is)] OK: $COUNT events on $KEY within window (threshold > $THRESHOLD)"
  fi

  sleep "$WINDOW_SEC"
done
