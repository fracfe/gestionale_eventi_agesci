# Regole iniziali di permessi e importi

## Permessi lato server

- EVENTS abilita l'accesso alle funzioni eventi.
- MY_EVENTS consente di leggere/modificare soltanto eventi di cui l'utente è responsabile; può assegnare nuovi eventi solo a sé.
- ALL_EVENTS consente di operare anche sugli altri eventi e assegnare responsabili diversi.
- SETTINGS riserva impostazioni e operazioni amministrative sui tipi evento/utenti. Non si deduce il privilegio dal nome del gruppo o dall'id1.
- DASHBOARD e EVENTS sono entrambi necessari per la pagina dashboard.
- Login e operazioni mutanti richiedono un token CSRF legato alla sessione; logout usa POST. Le richieste fetch dell'interfaccia includono il token automaticamente.
- Le operazioni utenti e tipi evento non ancora implementate restituiscono 501 invece di un falso successo. Profilo, cambio password e CRUD completi restano nel backlog.

La matrice è una base coerente con i permessi esistenti, da affinare con le regole educative/organizzative richieste. Non aggiunge automaticamente nuovi gruppi al database della beta.

## Centesimi

Importi e quote persistenti sono Numeric(14,2); il backend usa Decimal. Sono accettati punto e virgola decimali, anche per valori negativi. NaN, infinito, importi oltre l'intervallo e più di due decimali vengono rifiutati, senza arrotondamento silenzioso. L'autorizzazione sull'evento viene verificata prima di leggere o modificare i suoi dati.

Le formule lavorano con numeri decimali, mantenendo la compatibilità con le formule esistenti. L'eventuale regola per arrotondare risultati calcolati con frazioni di centesimo resta da definire prima dei rendiconti definitivi; non viene introdotto qui un arrotondamento commerciale implicito. Il JSON rappresenta Decimal come stringhe, mantenendo i centesimi. La migrazione conserva gli interi preesistenti come importi interi in euro: non li divide per100 e non può ricostruire centesimi già persi in passato.
