"""Upgrade da schema precedente con dati esistenti, senza db.create_all."""
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


BACKENDS = ['sqlite']
if os.environ.get('TEST_DATABASE_URL', '').startswith('mysql+pymysql:'):
    BACKENDS.append('mariadb')


@pytest.mark.parametrize('backend', BACKENDS)
def test_migrazione_conserva_dati_e_centesimi(tmp_path, backend):
    db_file = tmp_path / 'migration.sqlite'
    env = dict(os.environ, DB_TYPE='sqlite', DB_NAME=str(db_file), SECRET_KEY='migration-test')
    uri = 'sqlite:///' + str(db_file)
    if backend == 'mariadb':
        uri = os.environ['TEST_DATABASE_URL']
        url = make_url(uri)
        if not url.database.endswith('_test'):
            raise RuntimeError('Il database di migrazione deve terminare con _test')
        env.update(DB_TYPE='mariadb', DB_HOST=url.host, DB_PORT=str(url.port or 3306),
                   DB_USER=url.username, DB_PASSWORD=url.password or '', DB_NAME=url.database)
    engine = create_engine(uri)
    assert inspect(engine).get_table_names() == [], 'La migrazione richiede un database di prova vuoto' 
    def flask(*args, **extra):
        return subprocess.run([sys.executable, '-m', 'flask', *args], cwd=ROOT,
                              env=dict(env, **extra), capture_output=True, text=True)
    result = flask('db', 'upgrade', 'd324e2482509')
    assert result.returncode == 0, result.stderr
    result = flask('init-db', INITIAL_ADMIN_PASSWORD='migration-test-password')
    assert result.returncode == 0, result.stderr
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO tipi_eventi (id,nome) VALUES (1,'Campo')"))
        conn.execute(text("INSERT INTO eventi (id,nome,tipo,responsabile,stato,data_inizio,localita,iscritti,partecipanti,quota_acconto,quota_saldo,staff,iban) VALUES (1,'Campo',1,1,'PENDING','2026-01-01','Torino',1,1,12,34,1,'')"))
        conn.execute(text("INSERT INTO transazioni (id,tipo_transazione,evento,descrizione,data,importo) VALUES (1,1,1,'Quota','2026-01-01',12)"))
    result = flask('db', 'upgrade')
    assert result.returncode == 0, result.stderr
    columns = {c['name']: c['type'] for c in inspect(engine).get_columns('transazioni')}
    assert columns['importo'].scale == 2
    with engine.begin() as conn:
        assert conn.execute(text('SELECT importo FROM transazioni WHERE id=1')).scalar_one() == 12
        conn.execute(text('UPDATE transazioni SET importo=12.50 WHERE id=1'))
        assert Decimal(str(conn.execute(text('SELECT importo FROM transazioni WHERE id=1')).scalar_one())) == Decimal('12.50')
        assert conn.execute(text('SELECT quota_saldo FROM eventi WHERE id=1')).scalar_one() == 34
    result = flask('init-db', INITIAL_ADMIN_PASSWORD='another-test-password')
    assert result.returncode != 0 and 'già inizializzato' in result.stderr
    result = flask('db', 'downgrade', 'd324e2482509')
    assert result.returncode != 0 and 'Downgrade distruttivo bloccato' in result.stderr
    with engine.begin() as conn:
        assert Decimal(str(conn.execute(text('SELECT importo FROM transazioni WHERE id=1')).scalar_one())) == Decimal('12.50')
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)
    engine.dispose()
