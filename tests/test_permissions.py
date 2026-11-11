import pytest
from app import db
from models import Evento, Transazione
from conftest import csrf_token


def test_anonimo_non_legge_evento(app):
    assert app.test_client().get('/evento_data/2').status_code == 302


def test_login_richiede_csrf(app):
    response = app.test_client().post('/login', json={'username':'user1', 'passwd':'password-test'})
    assert response.status_code == 400
    assert response.json['response'] == 'csrf_invalid'


@pytest.mark.parametrize('path', ['/evento/3', '/evento_data/3', '/evento_data/3?tipo=transazioni', '/evento_data/3?tipo=rendiconto'])
def test_capo_non_legge_eventi_altrui(login_client, path):
    assert login_client(2).get(path).status_code == 403


def test_capo_lista_solo_propri_eventi(login_client):
    assert [event['id'] for event in login_client(2).get('/eventi_list').json['response']] == [2]


@pytest.mark.parametrize('method,path,payload', [
    ('post', '/evento_data/3?tipo=attiva', {}),
    ('post', '/evento_data/3?tipo=sottometti', {}),
    ('post', '/evento_data/3?tipo=update', {}),
    ('delete', '/evento_data/3?tipo=elimina', {}),
    ('post', '/transazioni/3', {'importo':'1.00'}),
])
def test_capo_non_modifica_eventi_altrui(app, login_client, method, path, payload):
    response = getattr(login_client(2), method)(path, json=payload)
    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(Evento, 3).stato == 'PENDING'
        assert Transazione.query.count() == 0


def test_admin_legge_altri_eventi(client):
    assert client.get('/evento_data/3').status_code == 200


@pytest.mark.parametrize('path', ['/system_option', '/impostazioni'])
def test_impostazioni_riservate(login_client, path):
    assert login_client(2).get(path).status_code == 403


def test_capo_non_assegna_evento_ad_altri(app, login_client):
    response = login_client(2).post('/eventi_list', json={'nome':'Nuovo', 'tipo_evento':1, 'account_responsabile':3})
    assert response.status_code == 403
    with app.app_context():
        assert Evento.query.count() == 3


def test_csrf_obbligatorio_anche_dopo_login(app):
    c = app.test_client()
    c.post('/login', json={'username':'user2', 'passwd':'password-test'}, headers={'X-CSRFToken': csrf_token(c)})
    assert c.post('/evento_data/2?tipo=attiva').status_code == 400
    with app.app_context():
        assert db.session.get(Evento, 2).stato == 'PENDING'


def test_csrf_di_altra_sessione_rifiutato(login_client):
    a, b = login_client(2), login_client(3)
    assert b.post('/evento_data/3?tipo=attiva', headers={'X-CSRFToken':csrf_token(a)}).status_code == 400


def test_logout_non_si_esegue_con_get(client):
    assert client.get('/logout').status_code == 405
    assert client.post('/logout').status_code == 302
    assert client.get('/evento_data/1').status_code == 302


def test_gruppo_senza_permessi(login_client):
    c = login_client(4)
    assert c.get('/eventi_list').status_code == 403
    assert c.get('/evento_data/1').status_code == 403
    assert c.get('/dashboard').status_code == 403


def test_capo_puo_creare_evento_proprio(app, login_client):
    response = login_client(2).post('/eventi_list', json={'nome':'Nuovo', 'tipo_evento':1, 'account_responsabile':2})
    assert response.json['status'] == 'success'
    with app.app_context():
        assert Evento.query.filter_by(nome='Nuovo').one().responsabile == 2


def test_capo_non_trasferisce_evento(app, login_client):
    payload = {'quota_acconto':'1.00', 'quota_saldo':'2.00', 'responsabile':3}
    assert login_client(2).post('/evento_data/2?tipo=update', json=payload).status_code == 403
    with app.app_context():
        assert db.session.get(Evento, 2).responsabile == 2


def test_operazioni_incomplete_non_fingono_successo(client):
    assert client.post('/user', json={}).status_code == 501
    assert client.delete('/user').status_code == 501
    assert client.delete('/tipi_eventi/1').status_code == 501
    assert client.post('/tipi_eventi', json={'tipo_id':'1','nome':'Nuovo'}).status_code == 501


def test_login_https_con_token_e_origin_corretto(app):
    import re
    c = app.test_client()
    page = c.get('/', base_url='https://example.test')
    token = re.search(r'name="csrf-token" content="([^"]+)"', page.text)[1]
    response = c.post('/login', base_url='https://example.test',
                      headers={'X-CSRFToken':token, 'Referer':'https://example.test/'},
                      json={'username':'user1','passwd':'password-test'})
    assert response.json['response'] == 'success'


def test_login_https_origin_estraneo_rifiutato(app):
    import re
    c = app.test_client()
    page = c.get('/', base_url='https://example.test')
    token = re.search(r'name="csrf-token" content="([^"]+)"', page.text)[1]
    response = c.post('/login', base_url='https://example.test',
                      headers={'X-CSRFToken':token, 'Referer':'https://other.test/'},
                      json={'username':'user1','passwd':'password-test'})
    assert response.status_code == 400
