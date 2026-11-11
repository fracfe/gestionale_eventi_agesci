from routes import eval_expr, calcola_formula

def test_eval_expr_ok():
    assert eval_expr("2+3*4") == 14

def test_eval_expr_blocca_codice():
    import pytest
    with pytest.raises(Exception):
        eval_expr("__import__('os').system('rm -rf /')")

def test_calcola_formula():
    formula = "[[a]]+[[b]]*2"
    variabili = {"a": 10, "b": 3}
    assert calcola_formula(formula, variabili) == 16

def test_calcola_formula_quota_staff_con_importi_decimali():
    from decimal import Decimal

    # Formula configurata da init_db per la quota dello staff.
    formula = "([[quota_acconto]]+[[quota_saldo]])/2"
    variabili = {
        "quota_acconto": Decimal("20.50"),
        "quota_saldo": Decimal("40.00"),
    }

    assert calcola_formula(formula, variabili) == 30.25

def test_calcola_formula_variabili_ripetute_con_prefisso_comune():
    formula = "([[quota]] + [[quota_saldo]]) * [[partecipanti]] - [[quota]]"
    variabili = {"quota": 12.5, "quota_saldo": 7.5, "partecipanti": 3}

    assert calcola_formula(formula, variabili) == 47.5

def test_calcola_formula_con_nomi_simili_e_segnaposto_ripetuto():
    formula = "([[quota]] - [[quota_acconto]]) * [[partecipanti]] + [[quota_acconto]]"
    variabili = {"quota": 25.5, "quota_acconto": 5.5, "partecipanti": 3}

    assert calcola_formula(formula, variabili) == 65.5

def test_calcola_formula_variabili_ripetute_e_nomi_simili():
    formula = "([[quota]] + [[quota_staff]]) * [[quota]]"
    variabili = {"quota": -2.5, "quota_staff": 10}

    assert calcola_formula(formula, variabili) == -18.75
