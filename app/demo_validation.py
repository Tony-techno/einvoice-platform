import copy

from app.extract_invoice import Invoice
from app.sample_data import GOOD_INVOICE
from app.validator import validate


def show(title, data):
    issues = validate(Invoice.model_validate(data))
    print(f"\n{title}: {'PASS' if not issues else 'FAIL'}")
    for i in issues:
        print(f"  [{i.rule}] {i.field}: {i.message}")


show("Good invoice", GOOD_INVOICE)

bad = copy.deepcopy(GOOD_INVOICE)
bad["supplier_trn"] = "12345"
bad["due_date"] = "2026-11-01"
bad["vat_amount"] = 300.0
bad["line_items"][0]["line_total"] = 1700.0
show("Bad invoice", bad)