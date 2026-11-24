#!/bin/sh
# One-off dump. Uses PG* env vars. Output: /backups/patchbeast-<UTC timestamp>.sql.gz
set -eu
mkdir -p /backups
OUT="/backups/patchbeast-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
pg_dump --no-owner --clean --if-exists | gzip -9 > "$OUT.tmp"
mv "$OUT.tmp" "$OUT"
# retention
find /backups -name 'patchbeast-*.sql.gz' -mtime +"${BACKUP_RETENTION_DAYS:-14}" -delete
echo "backup ok: $OUT ($(du -h "$OUT" | cut -f1))"
