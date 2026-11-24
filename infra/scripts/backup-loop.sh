#!/bin/sh
# Nightly pg_dump at 03:15 UTC. Runs forever inside the `backup` container.
set -u
touch /tmp/started_ok
while true; do
  now=$(date -u +%s)
  target=$(date -u -d "today 03:15" +%s 2>/dev/null || echo $((now + 86400)))
  [ "$target" -le "$now" ] && target=$((target + 86400))
  sleep $((target - now))
  /bin/sh /scripts/backup.sh || echo "BACKUP FAILED" >&2
done
