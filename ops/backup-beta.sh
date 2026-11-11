#!/bin/bash
# Backup esplicito della beta esistente; nessuna scansione NAS o pulizia storici.
set -euo pipefail
umask 077
root=${1:?Uso: backup-beta.sh /directory/backup-applicativi}
[[ -d "$root" && ! -L "$root" ]] || { echo 'Serve una directory reale esistente.' >&2; exit 1; }
backup=$(mktemp -d "$root/bilanci-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
# Password letta esclusivamente nel container, senza stamparla o passarla in argv.
docker exec bilanci-db sh -ec '
  export MYSQL_PWD="$MARIADB_PASSWORD"
  exec mariadb-dump --user="$MARIADB_USER" --single-transaction --skip-lock-tables \
    --routines --events --skip-comments --skip-extended-insert --order-by-primary "$MARIADB_DATABASE"
' > "$backup/database.sql"
[[ -s "$backup/database.sql" ]]
docker exec bilanci-db printenv MARIADB_DATABASE > "$backup/database-name"
docker inspect --format '{{.Name}} {{.Config.Image}} {{.Image}}' bilanci-web bilanci-db > "$backup/containers.txt"
(cd "$backup" && sha256sum database.sql > database.sha256)
printf 'Backup creato (ripristino ancora da verificare): %s\n' "$backup"
