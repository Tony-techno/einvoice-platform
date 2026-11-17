import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float


class Invoice(BaseModel):
    invoice_number: str
    issue_date: str
    due_date: str
    currency: str
    supplier_name: str
    supplier_trn: str
    buyer_name: str
    buyer_trn: str
    line_items: list[LineItem]
    subtotal: float
    vat_amount: float
    total_amount: float


PROMPT = (
    "Extract the invoice data from this image. Dates must be YYYY-MM-DD. "
    "Numbers must be plain numbers with no currency symbols or commas. "
    "Copy values exactly as printed. Do not calculate or correct anything."
)


def model_candidates():
    names = [os.getenv("GEMINI_MODEL"), "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
    seen, result = set(), []
    for n in names:
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result


def extract_from_bytes(data: bytes, mime_type: str = "image/png"):
    """Returns (Invoice, model_name_used). Raises RuntimeError if every model fails."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(api_version="v1beta", timeout=60000),
    )
    image = types.Part.from_bytes(data=data, mime_type=mime_type)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Invoice,
        temperature=0,
    )
    errors = []
    for name in model_candidates():
        try:
            response = client.models.generate_content(
                model=name, contents=[PROMPT, image], config=config
            )
            return Invoice.model_validate_json(response.text), name
        except Exception as e:
            errors.append(f"{name}: {type(e).__name__}")
    raise RuntimeError("All models failed (" + "; ".join(errors) + ")")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_invoices/invoice_001.png"
    try:
        invoice, used = extract_from_bytes(Path(path).read_bytes(), "image/png")
    except RuntimeError as e:
        raise SystemExit(str(e))
    print("Model used:", used)
    print(invoice.model_dump_json(indent=2))