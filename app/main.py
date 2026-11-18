import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

from app.extract_invoice import Invoice, extract_from_bytes
from app.fixer import diff_invoices, suggest_fix
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
    st.session_state.pop("fix", None)


def load_data(data: dict, note: str):
    st.session_state["invoice"] = data
    st.session_state["note"] = note
    st.session_state.pop("fix", None)


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

    st.divider()
    with st.expander("🛠 Report a problem / get a suggested fix", expanded=bool(issues)):
        st.write(
            "Describe what is wrong, attach a screenshot, or both. "
            "If the invoice already has validation errors, you can also just click the button."
        )
        report_text = st.text_area(
            "What is wrong?",
            key="report_text",
            placeholder="e.g. The supplier TRN is 100123456700003",
        )
        report_shot = st.file_uploader(
            "Screenshot (optional)", type=["png", "jpg", "jpeg"], key="report_shot"
        )

        if st.button("Suggest a fix"):
            if not report_text.strip() and report_shot is None and not issues:
                st.warning("Add a description or a screenshot first.")
            else:
                with st.spinner("Analysing the problem with Gemini..."):
                    try:
                        suggestion, model = suggest_fix(
                            data,
                            issues,
                            report_text,
                            report_shot.getvalue() if report_shot else None,
                            report_shot.type if report_shot else "image/png",
                        )
                    except Exception as e:
                        st.error(f"Could not get a suggestion: {e}")
                    else:
                        st.session_state["fix"] = {
                            "corrected": suggestion.corrected_invoice.model_dump(),
                            "explanation": suggestion.explanation,
                            "model": model,
                        }

        fix = st.session_state.get("fix")
        if fix:
            st.subheader("Suggested fix")
            st.write(fix["explanation"])

            changes = diff_invoices(data, fix["corrected"])
            if changes:
                st.write("Changes proposed:")
                st.dataframe(changes)
            else:
                st.info("No changes were suggested.")

            fixed_issues = validate(Invoice.model_validate(fix["corrected"]))
            if not fixed_issues:
                st.success("The corrected invoice passes all rules.")
            else:
                st.warning(f"The corrected invoice still has {len(fixed_issues)} problem(s):")
                st.dataframe(
                    [{"Rule": i.rule, "Field": i.field, "Problem": i.message} for i in fixed_issues]
                )

            st.caption(f"Suggested by {fix['model']}. Review the changes before applying.")
            if changes and st.button("Apply this fix"):
                st.session_state["invoice"] = fix["corrected"]
                st.session_state["note"] = "Corrected using an AI-suggested fix"
                st.session_state.pop("fix", None)
                st.rerun()