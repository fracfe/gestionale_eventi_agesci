from pathlib import Path
import subprocess
import os
import yaml
from app import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_separazione_sviluppo_beta():
    config = yaml.safe_load((ROOT / 'compose.development.yml').read_text())
    assert config['name'] == 'bilanci-development'
    assert config['services']['web']['ports'] == ['127.0.0.1:5001:8000']
    assert 'ports' not in config['services']['db']
    assert not any(v.get('external', False) for v in config['volumes'].values() if isinstance(v, dict))
    assert config['services']['web']['environment']['SESSION_COOKIE_NAME'] == 'bilanci_development'
    assert config['services']['db']['environment']['MARIADB_DATABASE'] == 'gestionale_development'


def test_creazione_segreti_non_sovrascrive(tmp_path):
    path = tmp_path / 'development.env'
    script = ROOT / 'ops/init-development.sh'
    first = subprocess.run(['bash', str(script), str(path)], capture_output=True)
    assert first.returncode == 0
    original = path.read_bytes()
    assert path.stat().st_mode & 0o077 == 0
    assert len(original.splitlines()) == 3
    assert subprocess.run(['bash', str(script), str(path)], capture_output=True).returncode != 0
    assert path.read_bytes() == original


def test_cookie_installazioni_indipendenti(monkeypatch):
    monkeypatch.setenv('SESSION_COOKIE_NAME', 'bilanci_development')
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI':'sqlite:///:memory:'})
    assert app.config['SESSION_COOKIE_NAME'] == 'bilanci_development'
    assert app.config['SESSION_COOKIE_HTTPONLY']
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'


def test_ci_test_pr_e_pubblicazione_condizionata():
    config = yaml.load((ROOT / '.github/workflows/python-tests.yml').read_text(), Loader=yaml.BaseLoader)
    assert 'pull_request' in config['on']
    assert config['jobs']['image']['needs'] == 'test'
    build = config['jobs']['image']['steps'][-1]
    assert build['with']['push'] == "${{ github.event_name == 'push' }}"
    assert 'calminaro' not in str(config)
