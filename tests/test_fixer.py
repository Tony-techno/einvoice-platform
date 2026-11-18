import copy

from app.fixer import diff_invoices
from app.sample_data import GOOD_INVOICE


def test_no_changes_gives_empty_diff():
    assert diff_invoices(GOOD_INVOICE, copy.deepcopy(GOOD_INVOICE)) == []


def test_changed_field_is_reported():
    new = copy.deepcopy(GOOD_INVOICE)
    new["vat_amount"] = 300.0
    assert diff_invoices(GOOD_INVOICE, new) == [
        {"Field": "vat_amount", "Before": "217.5", "After": "300.0"}
    ]


def test_changed_line_item_is_reported():
    new = copy.deepcopy(GOOD_INVOICE)
    new["line_items"][0]["line_total"] = 1700.0
    rows = diff_invoices(GOOD_INVOICE, new)
    assert rows[0]["Field"] == "line_items[1].line_total"