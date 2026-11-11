# Gestionale eventi AGESCI Piemonte

Gestione di eventi, quote e rendiconti. Fork di sviluppo di `calminaro/gestionale_eventi_agesci`.

## Ambienti

| Ambiente | Uso | Accesso |
|---|---|---|
| Sviluppo | Modifiche e dati di prova | Porta privata 5001 sulla VM108 |
| Beta | Collaudo della versione scelta | Porta 5000 e Funnel esistente |
| main | Codice consolidato | GitHub, con eventuale tag di versione |

Le due installazioni usano database, volumi, rete e cookie separati. Non si promuovono i dati di prova nella beta. La pubblicazione su GitHub non aggiorna automaticamente il sito.

**[Preparare lo sviluppo, aggiornare e recuperare](docs/AMBIENTI.md)** · **[Permessi e importi](docs/PERMESSI-E-IMPORTI.md)** · **[Backlog](BACKLOG.md)**

## Test

Python 3.12, MariaDB11.4 per le prove di integrazione; SQLite per test rapidi:

```bash
python -m venv .venv
.venv/bin/pip install -c constraints.txt -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest
node --test tests/csrf.test.cjs
```

Per eseguire la suite anche su un database MariaDB **dedicato e vuoto**, impostare `TEST_DATABASE_URL` con una URI `mysql+pymysql://.../gestionale_test`. La suite crea e cancella le proprie tabelle; rifiuta database non terminanti con `_test`. Non usare mai le credenziali o il database della beta. Le prove di migrazione coprono lo schema precedente con dati già presenti.

La CI esegue SQLite e MariaDB, verifica il codice JavaScript e costruisce l'immagine dopo i test. Pubblica nel registro del fork soltanto sui push in dev/main. GitHub Actions deve essere abilitato nel fork. Le dipendenze sono bloccate in `constraints.txt`.

## Avvio

La configurazione per il nuovo ambiente è `compose.development.yml`; seguire le istruzioni dedicate, incluso il plugin Docker Compose v2. Il comando `flask init-db` richiede una password amministrativa di almeno12caratteri e rifiuta un database con utenti già presenti. Non esistono credenziali predefinite.

La migrazione degli importi richiede backup e collaudo prima dell'applicazione alla beta. La configurazione e i segreti dell'installazione esistente restano fuori dal repository. La funzionalità Shell del controller per gli ambienti persistenti è distinta e ancora da implementare.

## Schema iniziale

Lo schema storico è illustrato in [static/schema_db.png](static/schema_db.png); per i tipi correnti fanno fede `models.py` e le migrazioni.
