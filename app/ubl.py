import xml.etree.ElementTree as ET

from app.extract_invoice import Invoice
from app.validator import validate

NS = {
    "": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}
for _prefix, _uri in NS.items():
    ET.register_namespace(_prefix, _uri)

# Illustrative value only: this is a demo, not an official PINT-AE submission.
CUSTOMIZATION_ID = "urn:peppol:pint:billing-1@ae-1"
VAT_PERCENT = "5"


def _q(prefix: str, tag: str) -> str:
    return f"{{{NS[prefix]}}}{tag}"


def _add(parent, prefix, tag, text=None, **attrs):
    el = ET.SubElement(parent, _q(prefix, tag), attrs)
    if text is not None:
        el.text = str(text)
    return el


def _money(value: float) -> str:
    return f"{value:.2f}"


def _party(parent, wrapper: str, name: str, trn: str) -> None:
    party = _add(_add(parent, "cac", wrapper), "cac", "Party")
    _add(_add(party, "cac", "PartyName"), "cbc", "Name", name)
    tax = _add(party, "cac", "PartyTaxScheme")
    _add(tax, "cbc", "CompanyID", trn)
    _add(_add(tax, "cac", "TaxScheme"), "cbc", "ID", "VAT")
    _add(_add(party, "cac", "PartyLegalEntity"), "cbc", "RegistrationName", name)


def _tax_category(parent, wrapper: str) -> None:
    cat = _add(parent, "cac", wrapper)
    _add(cat, "cbc", "ID", "S")
    _add(cat, "cbc", "Percent", VAT_PERCENT)
    _add(_add(cat, "cac", "TaxScheme"), "cbc", "ID", "VAT")


def build_ubl_xml(inv: Invoice) -> bytes:
    issues = validate(inv)
    if issues:
        details = "; ".join(f"[{i.rule}] {i.message}" for i in issues)
        raise ValueError("Invoice failed validation: " + details)

    cur = inv.currency.upper()
    root = ET.Element(_q("", "Invoice"))

    _add(root, "cbc", "CustomizationID", CUSTOMIZATION_ID)
    _add(root, "cbc", "ID", inv.invoice_number)
    _add(root, "cbc", "IssueDate", inv.issue_date)
    _add(root, "cbc", "DueDate", inv.due_date)
    _add(root, "cbc", "InvoiceTypeCode", "380")
    _add(root, "cbc", "DocumentCurrencyCode", cur)

    _party(root, "AccountingSupplierParty", inv.supplier_name, inv.supplier_trn)
    _party(root, "AccountingCustomerParty", inv.buyer_name, inv.buyer_trn)

    tax_total = _add(root, "cac", "TaxTotal")
    _add(tax_total, "cbc", "TaxAmount", _money(inv.vat_amount), currencyID=cur)
    sub = _add(tax_total, "cac", "TaxSubtotal")
    _add(sub, "cbc", "TaxableAmount", _money(inv.subtotal), currencyID=cur)
    _add(sub, "cbc", "TaxAmount", _money(inv.vat_amount), currencyID=cur)
    _tax_category(sub, "TaxCategory")

    totals = _add(root, "cac", "LegalMonetaryTotal")
    _add(totals, "cbc", "LineExtensionAmount", _money(inv.subtotal), currencyID=cur)
    _add(totals, "cbc", "TaxExclusiveAmount", _money(inv.subtotal), currencyID=cur)
    _add(totals, "cbc", "TaxInclusiveAmount", _money(inv.total_amount), currencyID=cur)
    _add(totals, "cbc", "PayableAmount", _money(inv.total_amount), currencyID=cur)

    for n, item in enumerate(inv.line_items, start=1):
        line = _add(root, "cac", "InvoiceLine")
        _add(line, "cbc", "ID", n)
        _add(line, "cbc", "InvoicedQuantity", f"{item.quantity:g}", unitCode="C62")
        _add(line, "cbc", "LineExtensionAmount", _money(item.line_total), currencyID=cur)
        product = _add(line, "cac", "Item")
        _add(product, "cbc", "Name", item.description)
        _tax_category(product, "ClassifiedTaxCategory")
        _add(_add(line, "cac", "Price"), "cbc", "PriceAmount", _money(item.unit_price), currencyID=cur)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)