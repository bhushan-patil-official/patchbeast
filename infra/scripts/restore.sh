#!/bin/sh
# Restore a gz dump into the running prod postgres. DESTRUCTIVE (drops and recreates objects).
set -eu
FILE="${1:?usage: restore.sh backups/<file>.sql.gz}"
[ -f "$FILE" ] || { echo "no such file: $FILE"; exit 1; }
printf "This REPLACES the live database with %s. Type 'yes' to continue: " "$FILE"
read -r ans; [ "$ans" = "yes" ] || { echo aborted; exit 1; }
C="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
$C stop api worker beat web
gunzip -c "$FILE" | $C exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
$C up -d
echo "restore complete"
