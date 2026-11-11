#!/bin/bash
# Crea soltanto il file dei segreti; non avvia servizi e non tocca la beta.
set -euo pipefail
umask 077
config=${1:?Uso: init-development.sh /percorso/nuovo/development.env}
if [[ -e "$config" || -L "$config" ]]; then
  echo "Il file esiste già: conservare le credenziali esistenti." >&2
  exit 1
fi
# noclobber evita sovrascritture anche in caso di esecuzioni concorrenti.
set -o noclobber
{
  printf 'DB_ROOT_PASSWORD=%s\n' "$(openssl rand -hex 32)"
  printf 'DB_PASSWORD=%s\n' "$(openssl rand -hex 24)"
  printf 'SECRET_KEY=%s\n' "$(openssl rand -hex 32)"
} > "$config"
printf 'Configurazione creata: %s\n' "$config"
