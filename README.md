# E-Invoice Platform (Demo)

![Tests](https://github.com/Tony-techno/einvoice-platform/actions/workflows/tests.yml/badge.svg)

A small demo that turns an invoice image into a validated, UAE-style e-invoice (UBL 2.1 XML), with an AI-assisted "Report a problem" feature that suggests fixes and checks them before they are applied.

> **Demo only.** This is a mock built on fake data. It is not an official UAE FTA / PINT-AE submission, and the XML has not been certified by any accredited provider.

## What it does

1. **Extracts** invoice fields (parties, TRNs, dates, line items, totals) from an image using the Gemini API.
2. **Validates** them against 11 business rules (TRN format, dates, line totals, 5% VAT, grand total).
3. **Generates** a UBL 2.1 XML invoice, only if the invoice passes validation.
4. **Suggests fixes** when something is wrong. You can describe the problem, attach a screenshot, or both. The AI proposes a correction, the app shows exactly what would change, the rules re-check the result, and nothing is applied until you click **Apply this fix**.

### Screenshots

A valid invoice, with the generated XML ready to download:

![Valid invoice](docs/screenshot_pass.png)

An invalid invoice, with each broken rule listed:

![Validation errors](docs/screenshot_errors.png)

## Try it in 5 minutes

You need Python 3.12 and Git.

```
git clone https://github.com/Tony-techno/einvoice-platform.git
cd einvoice-platform
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app/main.py
```

(On macOS or Linux, activate with `source .venv/bin/activate`.)

In the app, pick **Sample data, valid (no AI)** or **Sample data, with errors (no AI)**. Both work **without any API key**.

To use the AI features (reading an invoice image, suggesting fixes), get a free key from [Google AI Studio](https://aistudio.google.com), copy `.env.example` to `.env`, and put your key in it.

Run the tests (no key needed):

```
pip install -r requirements-dev.txt
python -m pytest -q
```

## Validation rules

| Rule | Check |
|---|---|
| R01 | Invoice number present |
| R02, R03 | Supplier and buyer TRN are exactly 15 digits |
| R04, R05 | Dates are valid; due date is not before issue date |
| R06 | Currency is AED |
| R07 | At least one line item |
| R08 | Line total = quantity x unit price |
| R09 | Subtotal = sum of line totals |
| R10 | VAT = 5% of subtotal |
| R11 | Total = subtotal + VAT |

These rules are a simplified demo, not the official rule set.

## Tech used

Python, Streamlit, Pydantic, Gemini API (free tier, with automatic fallback to a backup model when one is busy), UBL 2.1 XML, pytest, GitHub Actions (tests run on every push), Git/GitHub.

## Project structure

```
app/          the application (extraction, validation, XML, fixer, UI)
tests/        automated tests
scripts/      one-off diagnostic scripts
sample_invoices/  fake invoice used for the demo
docs/         screenshots and an example XML output
```

## Known limitations

- Uses the free Gemini tier, so the AI features can occasionally be slow or unavailable when the service is busy. The "no AI" options are unaffected.
- AI suggestions can be wrong, which is why every suggestion is re-validated and needs a click to apply.
- Use fake data only. Free-tier prompts may be used by Google to improve its products.

## Roadmap

Planned next: deploy to Google Cloud Run with automatic deploys from GitHub, log results to BigQuery, a scheduled daily summary, and further integrations. This section will be updated as each part is built.