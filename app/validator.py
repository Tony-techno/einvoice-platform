import re
from dataclasses import dataclass
from datetime import date

from app.extract_invoice import Invoice

TOLERANCE = 0.01
VAT_RATE = 0.05
TRN_PATTERN = re.compile(r"^\d{15}$")


@dataclass
class Issue:
    rule: str
    field: str
    message: str


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE


def _parse_date(value: str):
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate(inv: Invoice) -> list[Issue]:
    issues: list[Issue] = []

    def add(rule: str, field: str, message: str) -> None:
        issues.append(Issue(rule, field, message))

    if not inv.invoice_number.strip():
        add("R01", "invoice_number", "Invoice number is missing.")

    if not TRN_PATTERN.match(inv.supplier_trn):
        add("R02", "supplier_trn", f"Supplier TRN must be 15 digits, got '{inv.supplier_trn}'.")
    if not TRN_PATTERN.match(inv.buyer_trn):
        add("R03", "buyer_trn", f"Buyer TRN must be 15 digits, got '{inv.buyer_trn}'.")

    issue = _parse_date(inv.issue_date)
    due = _parse_date(inv.due_date)
    if issue is None:
        add("R04", "issue_date", f"Issue date '{inv.issue_date}' is not a valid YYYY-MM-DD date.")
    if due is None:
        add("R05", "due_date", f"Due date '{inv.due_date}' is not a valid YYYY-MM-DD date.")
    elif issue is not None and due < issue:
        add("R05", "due_date", "Due date is before the issue date.")

    if inv.currency.upper() != "AED":
        add("R06", "currency", f"Currency should be AED, got '{inv.currency}'.")

    if not inv.line_items:
        add("R07", "line_items", "Invoice has no line items.")

    for n, item in enumerate(inv.line_items, start=1):
        expected = round(item.quantity * item.unit_price, 2)
        if not _close(item.line_total, expected):
            add("R08", f"line_items[{n}]",
                f"Line total is {item.line_total}, but quantity x unit price = {expected}.")

    line_sum = round(sum(i.line_total for i in inv.line_items), 2)
    if not _close(inv.subtotal, line_sum):
        add("R09", "subtotal", f"Subtotal is {inv.subtotal}, but line totals add up to {line_sum}.")

    expected_vat = round(inv.subtotal * VAT_RATE, 2)
    if not _close(inv.vat_amount, expected_vat):
        add("R10", "vat_amount", f"VAT is {inv.vat_amount}, but 5% of subtotal is {expected_vat}.")

    expected_total = round(inv.subtotal + inv.vat_amount, 2)
    if not _close(inv.total_amount, expected_total):
        add("R11", "total_amount",
            f"Total is {inv.total_amount}, but subtotal + VAT = {expected_total}.")

    return issues