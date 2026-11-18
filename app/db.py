import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from app.extract_invoice import Invoice
from app.validator import validate

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(ROOT / "data" / "invoice_log.duckdb")
_lock = threading.Lock()

TOP_RULES_SQL = """
SELECT rule, COUNT(*) AS times_failed
FROM (
    SELECT unnest(string_split(rules, ',')) AS rule
    FROM events
    WHERE rules <> ''
)
GROUP BY rule
ORDER BY times_failed DESC, rule
"""


def _connect():
    try:
        path = Path(DB_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(path))
    except Exception:
        # Read-only folder (some hosts): fall back to the temp directory.
        con = duckdb.connect(str(Path(tempfile.gettempdir()) / "invoice_log.duckdb"))
    con.execute("CREATE SEQUENCE IF NOT EXISTS events_seq START 1")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id BIGINT DEFAULT nextval('events_seq'),
            ts TIMESTAMP,
            event_type VARCHAR,
            invoice_number VARCHAR,
            passed BOOLEAN,
            issue_count INTEGER,
            rules VARCHAR,
            model VARCHAR
        )
        """
    )
    return con


def log_event(event_type: str, invoice_data: dict, model: str = "") -> bool:
    """Record one action. Never raises, because logging must not break the app."""
    try:
        invoice = Invoice.model_validate(invoice_data)
        issues = validate(invoice)
        rules = ",".join(sorted({i.rule for i in issues}))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with _lock:
            con = _connect()
            try:
                con.execute(
                    "INSERT INTO events "
                    "(ts, event_type, invoice_number, passed, issue_count, rules, model) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [now, event_type, invoice.invoice_number, len(issues) == 0,
                     len(issues), rules, model or ""],
                )
            finally:
                con.close()
        return True
    except Exception:
        return False


def get_stats():
    """Returns summary numbers and tables for the Analytics section, or None on failure."""
    try:
        with _lock:
            con = _connect()
            try:
                total, passed = con.execute(
                    "SELECT COUNT(*), COUNT(*) FILTER (WHERE passed) FROM events"
                ).fetchone()
                top = con.execute(TOP_RULES_SQL).fetchall()
                recent = con.execute(
                    "SELECT strftime(ts, '%Y-%m-%d %H:%M:%S'), event_type, invoice_number, "
                    "passed, issue_count, rules FROM events ORDER BY id DESC LIMIT 10"
                ).fetchall()
            finally:
                con.close()
    except Exception:
        return None
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "top_rules": [{"Rule": r, "Times failed": n} for r, n in top],
        "recent": [
            {"Time (UTC)": t, "Event": e, "Invoice": inv, "Passed": p, "Issues": n, "Rules": r}
            for t, e, inv, p, n, r in recent
        ],
    }