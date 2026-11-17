from pathlib import Path

from app.extract_invoice import Invoice
from app.sample_data import GOOD_INVOICE
from app.ubl import build_ubl_xml

invoice = Invoice.model_validate(GOOD_INVOICE)
xml_bytes = build_ubl_xml(invoice)

out = Path("docs") / "example_ubl_invoice.xml"
out.write_bytes(xml_bytes)

print("Saved", out, "|", len(xml_bytes), "bytes")
print()
print(xml_bytes.decode("utf-8")[:700])