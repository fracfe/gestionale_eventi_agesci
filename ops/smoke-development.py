"""Collaudo HTTP con dati sintetici, esclusivamente sull'installazione development."""
import http.cookiejar
import json
import os
import re
from urllib.request import Request, HTTPCookieProcessor, build_opener
from uuid import uuid4

base = 'http://127.0.0.1:5001'
client = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
page = client.open(base).read().decode()
if 'Sviluppo · dati di prova' not in page:
    raise SystemExit('Ambiente development non riconosciuto: nessun dato modificato.')
token = re.search(r'name="csrf-token" content="([^"]+)"', page)[1]


def post(path, data):
    request = Request(base + path, data=json.dumps(data).encode(),
                      headers={'Content-Type': 'application/json', 'X-CSRFToken': token}, method='POST')
    result = json.load(client.open(request))
    assert result['status'] == 'success', result
    return result


assert post('/login', {'username':'admin', 'passwd':os.environ['SMOKE_PASSWORD']})['response'] == 'success'
post('/tipi_eventi', {'tipo_id':'', 'nome':'Tipo collaudo HTTP'})
types = json.load(client.open(base + '/tipi_eventi'))['response']
name = 'Collaudo HTTP ' + uuid4().hex
post('/eventi_list', {'nome':name, 'tipo_evento':types[-1]['id'], 'account_responsabile':1})
events = json.load(client.open(base + '/eventi_list'))['response']
event_id = next(event['id'] for event in events if event['nome'] == name)
for amount in ['12,50', '0.01']:
    post(f'/transazioni/{event_id}', {'tipo_transazione':1, 'descrizione':'Quota collaudo',
                                     'data':'2026-11-11', 'importo':amount})
report = json.load(client.open(base + f'/evento_data/{event_id}?tipo=rendiconto'))['response']
assert report['tot_entrate'] == '12.51', report
client.open(Request(base + '/logout', data=b'', headers={'X-CSRFToken':token}, method='POST')).read()
print('HTTP_SMOKE_PASSED: login, CSRF, evento, centesimi, rendiconto e logout.')
