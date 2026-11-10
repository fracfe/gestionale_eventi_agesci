# Prima delle nuove funzionalità

## Stato verificato

- Repository: `fracfe/gestionale_eventi_agesci`; sviluppo su `dev`.
- VM 108: ambiente del gestionale. VM 200: controller stable. VM 302: vecchio worker, escluso da questo lavoro.
- La beta sulla VM 108 usa il codice dev iniziale e7938158. Questa PR non aggiorna la VM.
- Cinque contributi di test riuniti nella PR #1: quattro casi delle formule e un caso di rifiuto di importo non numerico. Suite attesa: 10 test. Esecuzione completa ancora da verificare; il solo controllo della sintassi è superato.
- Il fork non espone Issues: il tentativo di apertura restituisce HTTP 410. Al controllo della PR non risultano esecuzioni Actions; verificare lo stato di abilitazione dalla pagina Actions.

## Preparazione necessaria

### 1. Verificare i test e correggere la CI

Eseguire la suite consolidata prima del merge. I workflow Docker di dev/main puntano ancora a `ghcr.io/calminaro/gestionale_eventi_agesci`, hanno un job build senza `needs: test` e tentano di pubblicare anche sulle pull request. Correggere il namespace del fork, pubblicare solo su push autorizzati dopo i test e verificare che Actions funzioni. I test sono duplicati tra workflow: riordinare senza perdere la verifica delle PR.

### 2. Rendere riproducibili aggiornamento e recupero

La VM usa `/opt/gestionale-bilanci`, configurazione riservata in `/etc/gestionale-bilanci`, container `bilanci-web` e `bilanci-db`, rete `bilanci`, volume `bilanci-db-data`. Il sito è associato a `127.0.0.1:5000` e pubblicato via Tailscale Funnel.

Preparare configurazione di deploy, versioni delle dipendenze/Python dichiarate, commit e immagine identificabili, procedura di aggiornamento e ritorno alla versione precedente. Prima di modifiche allo schema o dati reali, verificare backup MariaDB e ripristino in database separato. Non assumere la copertura dei backup della VM. Non rieseguire `init-db` su database inizializzato. Nessuna credenziale nel repository.

## Correzioni applicative prioritarie

### 3. Autorizzazioni

In `routes.py` diverse operazioni su eventi, transazioni e impostazioni hanno solo `login_required`, senza controlli espliciti di ruolo o appartenenza. Il controllo dashboard `if "DASHBOARD" and "EVENTS" in permessi` verifica solo EVENTS. I test attuali usano `LOGIN_DISABLED=True`.

Definire e applicare permessi lato server, testare con utenti e gruppi diversi e autenticazione abilitata, verificare protezione CSRF. Priorità prima di usare dati reali con più utenti.

### 4. Precisione degli importi

`models.py` usa Integer per importo delle transazioni e quote dell'evento, mentre le route accettano float. Definire Decimal/Numeric oppure centesimi interi e una migrazione verificata. Testare conservazione dei centesimi e totali su MariaDB: SQLite non garantisce lo stesso comportamento. Esempi: 12,50 e 0,01.

## Funzioni incomplete riscontrate

### 5. Profilo e gestione

- `templates/account.html`: contenuto main vuoto; richiama `static/account.js`, assente.
- Cambio password dall'interfaccia da implementare con verifica della password corrente e conferma della nuova.
- `/user`: POST e DELETE restituiscono successo senza eseguire operazioni.
- `/tipi_eventi`: DELETE non cancella; POST crea solo se tipo_id è vuoto, senza aggiornare i tipi esistenti.

Completare solo i flussi richiesti, con permessi lato server e test. Non restituire successo per operazioni non effettuate.

## Ordine proposto

1. Verifica e integrazione dei test consolidati.
2. CI del fork e procedura di aggiornamento/recupero.
3. Permessi e precisione monetaria.
4. Profilo/cambio password, utenti e tipi evento.
5. Ulteriori funzionalità definite con l'utente.

Le PR #1–#4 nel repository originale di Calminaro restano separate e non sono state chiuse o modificate.
