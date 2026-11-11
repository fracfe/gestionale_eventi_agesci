from decimal import Decimal
import pytest
from app import db
from models import Transazione
from money import parse_money
from routes import calcola_formula


@pytest.mark.parametrize('value,expected', [('12,50','12.50'),('0.01','0.01'),(12,'12.00'),('-2.35','-2.35')])
def test_parse_importi(value, expected):
    assert parse_money(value) == Decimal(expected)


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-Infinity', '1.001', '', None, True, '1000000000000'])
def test_importi_invalidi(value):
    with pytest.raises(ValueError):
        parse_money(value)


def test_formula_decimale_esatta():
    assert calcola_formula('[[a]]+[[b]]', {'a':Decimal('0.10'), 'b':Decimal('0.20')}) == Decimal('0.30')


def test_centesimi_persistenti(app, client):
    for value in ['12,50', '0.01']:
        response = client.post('/transazioni/1', json={'tipo_transazione':1, 'descrizione':'Quota',
                                                     'data':'2026-01-01', 'importo':value})
        assert response.json['status'] == 'success'
    with app.app_context():
        amounts = [item.importo for item in Transazione.query.order_by(Transazione.id)]
    assert amounts == [Decimal('12.50'), Decimal('0.01')]
    assert sum(amounts) == Decimal('12.51')
    assert client.get('/evento_data/1?tipo=rendiconto').json['response']['tot_entrate'] == '12.51'


def test_centesimi_extra_non_salvati(app, client):
    response = client.post('/transazioni/1', json={'importo':'12.501'})
    assert response.json['status'] == 'error'
    with app.app_context():
        assert Transazione.query.count() == 0


def test_quote_evento_persistono_centesimi(app, client):
    response = client.post('/evento_data/1?tipo=update', json={
        'nome_evento':'Campo', 'tipo_evento':1, 'responsabile':1,
        'data_inizio':'2026-01-01', 'data_fine':'2026-01-02', 'localita':'Torino',
        'iscritti':10, 'partecipanti':10, 'staff':2, 'iban':'',
        'quota_acconto':'12,50', 'quota_saldo':'0.01',
    })
    assert response.json['status'] == 'success'
    from models import Evento
    with app.app_context():
        event = db.session.get(Evento, 1)
        assert event.quota_acconto == Decimal('12.50')
        assert event.quota_saldo == Decimal('0.01')
