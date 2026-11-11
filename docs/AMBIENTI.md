# Sviluppo, beta e versioni consolidate

| Ambiente | Codice | Database | Accesso |
|---|---|---|---|
| Sviluppo | ramo di lavoro o dev | nuovo database development | VM108, porta locale 5001, accesso privato |
| Beta esistente | commit scelto per collaudo | bilanci-db e volume bilanci-db-data | porta locale 5000, Funnel attuale |
| Versione consolidata | main e tag | nessun terzo database obbligatorio | GitHub |

Gli aggiornamenti del repository non aggiornano automaticamente i container.
La promozione riguarda il codice, non la copia dei dati di sviluppo nella beta.
La beta e Funnel esistenti non sono modificati dai file di questa consegna.

## Preparare lo sviluppo sulla VM108

Prerequisiti: Docker, plugin `docker compose` v2, Git, OpenSSL. La sola installazione di docker.io non garantisce il plugin Compose: verificare `docker compose version` e installare il plugin dai pacchetti supportati per Debian prima di procedere.

Usare un checkout dedicato, per non spostare il checkout attualmente usato per la beta:

```bash
git clone --branch dev https://github.com/fracfe/gestionale_eventi_agesci.git /opt/gestionale-bilanci-development
cd /opt/gestionale-bilanci-development
install -d -m 700 /etc/gestionale-bilanci-development
bash ops/init-development.sh /etc/gestionale-bilanci-development/development.env
export VCS_REF=$(git rev-parse HEAD)
docker compose --env-file /etc/gestionale-bilanci-development/development.env -f compose.development.yml config --quiet
docker compose --env-file /etc/gestionale-bilanci-development/development.env -f compose.development.yml build
docker compose --env-file /etc/gestionale-bilanci-development/development.env -f compose.development.yml up -d db
```

Solo alla prima inizializzazione del nuovo database, creare l'amministratore. La password viene richiesta due volte, senza essere mostrata. Il comando rifiuta un database con utenti già presenti e non imposta una password predefinita.

```bash
docker compose --env-file /etc/gestionale-bilanci-development/development.env -f compose.development.yml run --rm --entrypoint sh web -ec 'flask db upgrade && flask init-db'
docker compose --env-file /etc/gestionale-bilanci-development/development.env -f compose.development.yml up -d web
curl --fail http://127.0.0.1:5001/health
```

Dal PC aprire un tunnel SSH:

```bash
ssh -L 5001:127.0.0.1:5001 root@192.168.10.52
```

Poi aprire `http://localhost:5001`. Il sito di sviluppo usa un cookie proprio, oltre a rete, database e volume separati. Il suo accesso web non richiede l'apertura della porta sulla LAN o la modifica di Funnel. Non usare la porta 6000: alcuni browser la bloccano. Sulla VM con 2GB misurare `docker stats`; se necessario fermare lo sviluppo quando non serve (`compose ... stop`, senza `down -v`).

## Provare un aggiornamento nello sviluppo

1. Scegliere un ramo/commit esatto e avere il checkout pulito.
2. Eseguire test e revisione; annotare SHA.
3. Ricostruire lo sviluppo con `VCS_REF` uguale allo SHA e `compose ... up -d --build web`.
4. Verificare `/health`, login, creazione evento, importi e autorizzazioni. Le migrazioni girano sul solo DB development.
5. Collaudare nella beta solo su richiesta esplicita. Dopo il collaudo, promuovere lo stesso commit approvato in main/tag; le correzioni devono tornare anche in dev.

## Backup e prova di ripristino della beta

Gli script non cercano backup esistenti o NAS e non impostano cancellazioni o pianificazioni.

```bash
install -d -m 700 /var/backups/gestionale-bilanci
bash ops/backup-beta.sh /var/backups/gestionale-bilanci
# Usare esattamente la directory restituita:
bash ops/restore-drill.sh /var/backups/gestionale-bilanci/bilanci-DATA-SUFFISSO
```

Il backup conserva un dump SQL, checksum, nome database e identificatori delle immagini. I segreti `/etc/gestionale-bilanci` e l'immagine effettivamente usata vanno conservati separatamente in modo riservato: il solo dump non ricostruisce l'installazione. Verificare inoltre la copertura dei backup VM del proprio homelab senza darla per scontata.

La pipeline verifica anche questa sequenza su container effimeri del runner. La prova sulla VM108 resta separata. La prova avvia MariaDB in un nuovo volume, senza rete e senza porte pubblicate. Importa il dump e lo esporta nuovamente: `RESTORE_VERIFIED` richiede lo stesso checksum del dump deterministico. Solo dopo successo elimina i propri container/volume temporanei; su fallimento li conserva. Richiede RAM e spazio per un secondo database: eseguirla a sviluppo fermo sulla VM da2GB. Non ripristina mai nella beta.

## Prima di aggiornare la beta

Questo cambiamento contiene una migrazione Integer→Numeric(14,2). Prima di applicarla: backup verificato, immagine vecchia conservata e collaudo su MariaDB. Per una prova di recupero completa servono anche i segreti e l'immagine della versione precedente. Non basta rinominare un container dopo una migrazione.

- Registrare SHA, immagine attuale e nuova immagine identificata dallo SHA.
- Fermare le scritture della beta durante il backup finale e la migrazione.
- Eseguire `flask db upgrade` una volta con la nuova immagine e la configurazione della beta; non eseguire `init-db`.
- Avviare la nuova immagine mantenendo rete bilanci, configurazione della beta e associazione 127.0.0.1:5000→8000. Configurare `COOKIE_SECURE=1` per il solo accesso HTTPS Funnel.
- Verificare health, login, dati e URL pubblico prima di riaprire l'accesso.
- Se il codice precedente non è compatibile con lo schema nuovo, recuperare in un database separato il backup pre-migrazione e usare l'immagine corrispondente. Il downgrade automatico a Integer è bloccato per non perdere centesimi. Una copia ripristinata non include le scritture successive al backup.

Non è stato effettuato un aggiornamento della beta o una prova di recupero sul suo database da questa consegna.
