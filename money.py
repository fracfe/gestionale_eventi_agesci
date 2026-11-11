"""Importi in euro: centesimi esatti, senza conversioni float."""
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")
MAX_MONEY = Decimal("999999999999.99")


def parse_money(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("importo non valido")
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
        if not amount.is_finite() or abs(amount) > MAX_MONEY:
            raise ValueError("importo fuori intervallo")
        result = amount.quantize(CENT)
        if amount != result:
            raise ValueError("Sono ammessi al massimo due decimali")
        return result
    except InvalidOperation as error:
        raise ValueError("importo non valido") from error
