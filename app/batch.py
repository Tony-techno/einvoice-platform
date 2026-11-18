import copy
import random

import duckdb

from app.extract_invoice import Invoice
from app.sample_data import GOOD_INVOICE
from app.ubl import build_ubl_xml
from app.validator import validate


def _wrong_vat(d):
    d["vat_amount"] = 300.0


def _bad_trn(d):
    d["supplier_trn"] = "12345"


def _bad_total(d):
    d["total_amount"] = round(d["total_amount"] + 10, 2)


def _due_before_issue(d):
    d["due_date"] = "2026-11-01"


def _bad_line(d):
    d["line_items"][0]["line_total"] = round(d["line_items"][0]["line_total"] - 100, 2)


DEFECTS = [_wrong_vat, _bad_trn, _bad_total, _due_before_issue, _bad_line]

TOP_RULES_SQL = """
SELECT rule, COUNT(*) AS times_failed
FROM (
    SELECT unnest(string_split(rules, ',')) AS rule
    FROM results
    WHERE rules <> ''
)
GROUP BY rule
ORDER BY times_failed DESC, rule
"""


def make_batch(day: str, size: int = 8) -> list[dict]:
    """Synthetic invoices for a given day. The same day always gives the same batch."""
    rng = random.Random(day)
    batch = []
    defective = 0
    for n in range(1, size + 1):
        inv = copy.deepcopy(GOOD_INVOICE)
        inv["invoice_number"] = f"INV-{day.replace('-', '')}-{n:03d}"
        if rng.random() < 0.4:
            rng.choice(DEFECTS)(inv)
            defective += 1
        batch.append(inv)
    if defective == 0:
        DEFECTS[0](batch[-1])
    return batch


def process_batch(batch: list[dict]):
    """Validate each invoice; build XML for the valid ones."""
    results = []
    xml_files = {}
    for data in batch:
        inv = Invoice.model_validate(data)
        issues = validate(inv)
        if not issues:
            xml_files[inv.invoice_number] = build_ubl_xml(inv)
        results.append({
            "invoice_number": inv.invoice_number,
            "passed": not issues,
            "issue_count": len(issues),
            "rules": ",".join(sorted({i.rule for i in issues})),
        })
    return results, xml_files


def summarise(results: list[dict]) -> dict:
    """Summary numbers computed with SQL in an in-memory DuckDB."""
    con = duckdb.connect(":memory:")
    try:
        con.execute(
            "CREATE TABLE results (invoice_number VARCHAR, passed BOOLEAN, "
            "issue_count INTEGER, rules VARCHAR)"
        )
        con.executemany(
            "INSERT INTO results VALUES (?, ?, ?, ?)",
            [[r["invoice_number"], r["passed"], r["issue_count"], r["rules"]] for r in results],
        )
        total, passed = con.execute(
            "SELECT COUNT(*), COUNT(*) FILTER (WHERE passed) FROM results"
        ).fetchone()
        top = con.execute(TOP_RULES_SQL).fetchall()
    finally:
        con.close()
    return {"total": total, "passed": passed, "failed": total - passed, "top_rules": top}


def render_report(generated: str, summary: dict, results: list[dict], xml_count: int) -> str:
    lines = [
        "# Daily summary",
        "",
        f"Generated: {generated}. Synthetic sample invoices (demo data only).",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Invoices processed | {summary['total']} |",
        f"| Passed validation | {summary['passed']} |",
        f"| Failed validation | {summary['failed']} |",
        f"| UBL XML files generated | {xml_count} |",
        "",
        "## Most common rule failures",
        "",
    ]
    if summary["top_rules"]:
        lines += ["| Rule | Times failed |", "|---|---|"]
        lines += [f"| {rule} | {count} |" for rule, count in summary["top_rules"]]
    else:
        lines.append("No rule failures today.")
    lines += ["", "## Per-invoice results", "", "| Invoice | Result | Rules failed |", "|---|---|---|"]
    for r in results:
        lines.append(
            f"| {r['invoice_number']} | {'PASS' if r['passed'] else 'FAIL'} | {r['rules'] or '-'} |"
        )
    return "\n".join(lines) + "\n"