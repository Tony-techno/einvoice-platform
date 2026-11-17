import copy
import xml.etree.ElementTree as ET

import pytest

from app.extract_invoice import Invoice
from app.sample_data import GOOD_INVOICE
from app.ubl import NS, build_ubl_xml

CBC = {"cbc": NS["cbc"], "cac": NS["cac"]}


def test_xml_is_well_formed_and_has_invoice_number():
    root = ET.fromstring(build_ubl_xml(Invoice.model_validate(GOOD_INVOICE)))
    assert root.find("cbc:ID", CBC).text == "INV-2026-0042"


def test_payable_amount_and_line_count():
    root = ET.fromstring(build_ubl_xml(Invoice.model_validate(GOOD_INVOICE)))
    payable = root.find("cac:LegalMonetaryTotal/cbc:PayableAmount", CBC)
    assert payable.text == "4567.50"
    assert payable.attrib["currencyID"] == "AED"
    assert len(root.findall("cac:InvoiceLine", CBC)) == 3


def test_invalid_invoice_is_refused():
    data = copy.deepcopy(GOOD_INVOICE)
    data["vat_amount"] = 300.0
    with pytest.raises(ValueError):
        build_ubl_xml(Invoice.model_validate(data))