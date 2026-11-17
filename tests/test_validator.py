import copy

from app.extract_invoice import Invoice
from app.sample_data import GOOD_INVOICE
from app.validator import validate


def rules_for(data):
    return {i.rule for i in validate(Invoice.model_validate(data))}


def test_good_invoice_passes():
    assert rules_for(GOOD_INVOICE) == set()


def test_wrong_vat_is_caught():
    data = copy.deepcopy(GOOD_INVOICE)
    data["vat_amount"] = 300.0
    assert "R10" in rules_for(data)


def test_bad_trn_is_caught():
    data = copy.deepcopy(GOOD_INVOICE)
    data["supplier_trn"] = "12345"
    assert "R02" in rules_for(data)


def test_due_date_before_issue_is_caught():
    data = copy.deepcopy(GOOD_INVOICE)
    data["due_date"] = "2026-11-01"
    assert "R05" in rules_for(data)