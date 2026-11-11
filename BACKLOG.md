# Backlog del gestionale eventi

Aggiornato l’11 novembre2026. Unico elenco delle attività applicative; lo sviluppo del controller ha un proprio backlog separato.

## Stato degli ambienti

- Repository corretto: `fracfe/gestionale_eventi_agesci`. Rami di lavoro → dev → beta scelta esplicitamente → main/tag dopo il collaudo.
- VM108: gestionale e beta; VM200: controller stable; VM302: vecchio worker, escluso da questi interventi.
- La beta continua a usare il codice e7938158. Non è stata aggiornata e i suoi dati/configurazione/Funnel non sono stati modificati.
- PR1 integrata in dev al commit dd1cb1d: cinque contributi di test consolidati, 10testPASS sulla VM108 in container temporaneo/SQLite. Le PR1–4 nel repository originale restano separate.

## Preparazione dello sviluppo

### F01 — CI e immagini del fork

Implementata una sola pipeline per PR/push in dev/main: suite SQLite+MariaDB11.4, test JavaScript, verifica Compose, build dopo i test. Push immagini solo per eventi push nel registro ricavato dal nome del fork. Rimossi i workflow duplicati diretti al registro di Calminaro. Python3.12 e dipendenze bloccate.

**Da verificare sul servizio:** abilitazione GitHub Actions e run effettivo sul fork, inclusi build Docker e pubblicazione GHCR. Al controllo precedente non risultavano run. Issues è disabilitato (HTTP410): riabilitarlo se si vuole migrare questo elenco nel tracker, senza mantenere due liste concorrenti.

### F02 — Ambiente di sviluppo indipendente

Preparati `compose.development.yml` e generatore dei segreti senza sovrascrittura. Porta127.0.0.1:5001, database/volume/rete dedicati, cookie `bilanci_development`, indicazione visibile “Sviluppo · dati di prova”. Accesso da browser con tunnel SSH; il Funnel della beta resta invariato. `/health` controlla l’accessibilità delle tabelle applicative.

**Da attivare sulla VM108:** installare/verificare Composev2, creare checkout separato, inizializzare nuovo database e provare l’interfaccia. I2GB di RAM richiedono misura dei consumi e, se necessario, sviluppo fermo quando non serve. Nessuna installazione della nuova configurazione dichiarata eseguita.

### F03 — Backup, ripristino e promozione

Preparati `ops/backup-beta.sh`, `ops/restore-drill.sh` e procedura in `docs/AMBIENTI.md`: dump deterministico/checksum/immagini, recupero in database temporaneo senza rete e confronto dopo importazione. La promozione mantiene i dati della beta; backup prima di migrazioni e ritorno alla coppia immagine+schema compatibile. Nessuna scansione NAS o rotazione automatica.

**Da collaudare sulla VM108:** backup effettivo, prova del ripristino con Docker e conservazione separata di segreti/immagine. I backup della VM non sono stati verificati. Non rieseguire init-db. Nessuna operazione sui backup o sul database della beta svolta dalla chat.

## Correzioni applicative

### F04 — Importi esatti

Implementati Numeric(14,2) per importi/quote, conversioni Decimal e formule decimali. Input con più di2decimali, non finito o fuori intervallo rifiutato. Migrazione da schema precedente conserva dati e valori in euro; downgrade distruttivo a Integer rifiutato. Regole e limiti in `docs/PERMESSI-E-IMPORTI.md`.

**Prima della beta:** collaudo di migrazione su copia recuperabile del suo database. I centesimi eventualmente persi nello schema precedente non sono ricostruibili. Definire la regola per risultati calcolati con frazioni di centesimo prima dei rendiconti definitivi.

### F05 — Autorizzazioni e richieste mutanti

Implementati controlli lato server per EVENTS, MY_EVENTS/ALL_EVENTS e proprietà evento, assegnazioni del responsabile e SETTINGS. Dashboard richiede entrambi i permessi previsti. Test con utenti diversi e login attivo. Protezione CSRF su login e mutazioni, token automatico nelle fetch della UI, logoutPOST. Nessun gruppo o utente della beta modificato.

**Da collaudare nello sviluppo:** flussi web con gruppi reali e conferma della matrice organizzativa. La protezione della beta attuale non cambia finché non viene aggiornata esplicitamente.

## Funzionalità successive

### U01 — Profilo e password

Pagina Profilo ancora vuota; eliminare il riferimento al file account.js assente o realizzarlo con la funzione. Implementare cambio password con password attuale e conferma della nuova, poi verificare gestione sessioni.

### U02 — Utenti e tipi evento

Completare creazione/modifica/cancellazione utenti e modifica/cancellazione tipi evento con permessi e gestione dei riferimenti in uso. Le operazioni non implementate ora restituiscono501 invece di un falso successo.

### U03 — Validazioni e flussi contabili

Ampliare validazioni di campi obbligatori/date/stati, gestione degli errori della UI e criteri di transizione PENDING/ACTIVE/SUBMIT/DONE. Definire requisiti di grafici/esportazioni, senza ricavare nuove funzionalità dai soli placeholder.

## Confini della consegna

Modifiche al codice in dev, senza promozione in main o aggiornamento beta. La Shell per registrare e amministrare ambienti persistenti esistenti è D14 del backlog controller: non è implementata da questa consegna e non è un prerequisito per scrivere/testare il codice del gestionale.
