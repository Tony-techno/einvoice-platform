import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

from app.extract_invoice import Invoice, extract_from_bytes
from app.sample_data import GOOD_INVOICE
from app.ubl import build_ubl_xml
from app.validator import validate

SAMPLE_IMAGE = ROOT / "sample_invoices" / "invoice_001.png"

st.set_page_config(page_title="E-Invoice Platform", page_icon="🧾", layout="wide")
st.title("🧾 E-Invoice Platform (Demo)")
st.caption(
    "Invoice image → AI extracts the fields → rules validate them → UBL 2.1 XML. "
    "This is a mock of UAE-style e-invoicing for demonstration. Use fake data only."
)

with st.sidebar:
    st.header("About")
    st.write(
        "Built with Python, Streamlit and the Gemini API. "
        "The XML follows the UBL 2.1 structure but is not an official PINT-AE submission."
    )
    st.write("Tip: the two 'without AI' options work even if the AI service is busy.")


def run_extraction(data: bytes, mime: str):
    with st.spinner("Reading the invoice with Gemini..."):
        try:
            invoice, model = extract_from_bytes(data, mime)
        except Exception as e:
            st.error(f"Could not read the invoice: {e}")
            return
    st.session_state["invoice"] = invoice.model_dump()
    st.session_state["note"] = f"Extracted by {model}"


def load_data(data: dict, note: str):
    st.session_state["invoice"] = data
    st.session_state["note"] = note


OPTIONS = [
    "Upload an invoice image",
    "Use the sample invoice image (AI)",
    "Sample data, valid (no AI)",
    "Sample data, with errors (no AI)",
]
choice = st.radio("Choose an input", OPTIONS)

if choice == OPTIONS[0]:
    uploaded = st.file_uploader("Invoice image (PNG or JPG)", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        st.image(uploaded.getvalue(), width=350)
        if st.button("Extract and validate"):
            run_extraction(uploaded.getvalue(), uploaded.type or "image/png")

elif choice == OPTIONS[1]:
    if SAMPLE_IMAGE.exists():
        st.image(str(SAMPLE_IMAGE), width=350)
        if st.button("Extract and validate"):
            run_extraction(SAMPLE_IMAGE.read_bytes(), "image/png")
    else:
        st.warning("Sample image not found. Run: python app\\make_sample_invoice.py")

elif choice == OPTIONS[2]:
    if st.button("Load sample data"):
        load_data(copy.deepcopy(GOOD_INVOICE), "Built-in sample data (no AI call)")

else:
    if st.button("Load sample data with errors"):
        bad = copy.deepcopy(GOOD_INVOICE)
        bad["supplier_trn"] = "12345"
        bad["due_date"] = "2026-11-01"
        bad["vat_amount"] = 300.0
        bad["line_items"][0]["line_total"] = 1700.0
        load_data(bad, "Built-in sample data with deliberate errors (no AI call)")

data = st.session_state.get("invoice")
if data:
    st.divider()
    st.caption(st.session_state.get("note", ""))
    invoice = Invoice.model_validate(data)
    issues = validate(invoice)

    left, right = st.columns(2)

    with left:
        st.subheader("Extracted data")
        st.json({k: v for k, v in data.items() if k != "line_items"})
        st.write("Line items")
        st.dataframe(data["line_items"])

    with right:
        st.subheader("Validation")
        if not issues:
            st.success("All rules passed.")
            xml_bytes = build_ubl_xml(invoice)
            st.download_button(
                "Download UBL XML",
                data=xml_bytes,
                file_name=f"{invoice.invoice_number}.xml",
                mime="application/xml",
            )
            st.code(xml_bytes.decode("utf-8"), language="xml")
        else:
            st.error(f"{len(issues)} problem(s) found. XML is only generated for valid invoices.")
            st.dataframe(
                [{"Rule": i.rule, "Field": i.field, "Problem": i.message} for i in issues]
            )