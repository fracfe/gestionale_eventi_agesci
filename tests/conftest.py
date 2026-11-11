import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DB_TYPE', 'sqlite')
os.environ.setdefault('DB_NAME', ':memory:')
os.environ.setdefault('SECRET_KEY', 'test-bootstrap-only')

import pytest
from werkzeug.security import generate_password_hash
from app import create_app, db
from models import User, GruppiUser, Evento, TipoEvento, TipoTransazione


@pytest.fixture
def app():
    uri = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    if not uri.startswith('sqlite:') and not uri.rsplit('/', 1)[-1].endswith('_test'):
        raise RuntimeError('Il database di test deve terminare con _test')
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': uri})
    with app.app_context():
        db.create_all()
        db.session.add_all([
            GruppiUser(id=1, name='admin', permessi=['EVENTS', 'DASHBOARD', 'ALL_EVENTS', 'MY_EVENTS', 'SETTINGS', 'ACCOUNT']),
            GruppiUser(id=2, name='capo', permessi=['EVENTS', 'DASHBOARD', 'MY_EVENTS', 'ACCOUNT']),
            GruppiUser(id=3, name='senza-permessi', permessi=[]),
        ])
        db.session.flush()
        for uid, group in [(1,1), (2,2), (3,2), (4,3)]:
            db.session.add(User(id=uid, username=f'user{uid}', password=generate_password_hash('password-test'),
                                nome='Nome', cognome='Cognome', mail=f'user{uid}@example.test', gruppo=group))
        db.session.add(TipoEvento(id=1, nome='Campo'))
        db.session.add(TipoTransazione(id=1, nome='E1', tipo='E', descrizione='Quota', calcolata=False, formula=''))
        db.session.flush()
        for eid, owner in [(1,1), (2,2), (3,3)]:
            db.session.add(Evento(id=eid, nome=f'Evento {eid}', tipo=1, responsabile=owner,
                                 stato='PENDING', data_inizio=date(2026,1,1), localita='Torino',
                                 iscritti=1, partecipanti=1, quota_acconto=0, quota_saldo=0, staff=1, iban=''))
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def csrf_token(client):
    response = client.get('/')
    if response.status_code == 302:
        response = client.get('/account')
    return re.search(r'name="csrf-token" content="([^"]+)"', response.text)[1]


@pytest.fixture
def login_client(app):
    def make(user_id=1):
        client = app.test_client()
        token = csrf_token(client)
        response = client.post('/login', json={'username': f'user{user_id}', 'passwd': 'password-test'},
                               headers={'X-CSRFToken': token})
        assert response.json['response'] == 'success'
        client.environ_base['HTTP_X_CSRFTOKEN'] = csrf_token(client)
        return client
    return make


@pytest.fixture
def client(login_client):
    return login_client(1)
