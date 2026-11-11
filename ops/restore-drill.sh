#!/bin/bash
# Ripristino SOLO in un nuovo database usa-e-getta; non usa la rete della beta.
set -euo pipefail
umask 077
backup=$(realpath "${1:?Uso: restore-drill.sh /directory/backup}")
(cd "$backup" && sha256sum --check database.sha256)
database=$(cat "$backup/database-name")
[[ "$database" =~ ^[A-Za-z0-9_]+$ ]] || { echo 'Nome database non valido.' >&2; exit 1; }
work=$(mktemp -d /tmp/bilanci-restore.XXXXXXXX)
name="bilanci-restore-${work##*.}"
volume="$name-data"
printf 'MARIADB_ROOT_PASSWORD=%s\nMARIADB_DATABASE=%s\n' "$(openssl rand -hex 32)" "$database" > "$work/db.env"
success=0
created_container=0
created_volume=0
cleanup() {
  if [[ "$success" == 1 ]]; then
    [[ "$created_container" == 0 ]] || docker rm -f "$name" >/dev/null
    [[ "$created_volume" == 0 ]] || docker volume rm "$volume" >/dev/null
    rm -f "$work/db.env"
    rmdir "$work"
  else
    printf 'Prova incompleta; conservati solo i dati della prova: container=%s volume=%s config=%s\n' "$name" "$volume" "$work" >&2
  fi
}
trap cleanup EXIT
docker volume create --label bilanci-purpose=restore-drill "$volume" >/dev/null
created_volume=1
docker run -d --name "$name" --network none --env-file "$work/db.env" \
  --mount "type=volume,source=$volume,target=/var/lib/mysql" \
  --health-cmd='healthcheck.sh --connect --innodb_initialized' \
  --health-interval=3s --health-timeout=3s --health-retries=40 mariadb:11.4 >/dev/null
created_container=1
ready=0
for attempt in $(seq 1 60); do
  if [[ "$(docker inspect -f '{{.State.Health.Status}}' "$name")" == healthy ]]; then ready=1; break; fi
  sleep 2
done
[[ "$ready" == 1 ]] || { echo 'Database della prova non pronto.' >&2; exit 1; }
docker exec -i "$name" sh -ec 'export MYSQL_PWD="$MARIADB_ROOT_PASSWORD"; exec mariadb -uroot "$MARIADB_DATABASE"' < "$backup/database.sql"
restored=$(docker exec "$name" sh -ec '
  export MYSQL_PWD="$MARIADB_ROOT_PASSWORD"
  exec mariadb-dump -uroot --single-transaction --skip-lock-tables --routines --events \
    --skip-comments --skip-extended-insert --order-by-primary "$MARIADB_DATABASE"
' | sha256sum | cut -d ' ' -f 1)
original=$(cut -d ' ' -f 1 "$backup/database.sha256")
[[ "$restored" == "$original" ]] || { echo 'Confronto dump fallito: prova conservata per analisi.' >&2; exit 1; }
success=1
printf 'RESTORE_VERIFIED: schema e dati ridumpati identici al backup.\n'
