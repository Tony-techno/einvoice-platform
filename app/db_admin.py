import csv
import io

from app import db


def export_csv() -> str:
    """All logged events as CSV text, or an empty string if anything fails."""
    try:
        with db._lock:
            con = db._connect()
            try:
                rows = con.execute(
                    "SELECT strftime(ts, '%Y-%m-%d %H:%M:%S'), event_type, invoice_number, "
                    "passed, issue_count, rules, model FROM events ORDER BY id"
                ).fetchall()
            finally:
                con.close()
    except Exception:
        return ""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["time_utc", "event_type", "invoice_number", "passed", "issue_count", "rules", "model"])
    writer.writerows(rows)
    return buffer.getvalue()


def clear_events() -> bool:
    try:
        with db._lock:
            con = db._connect()
            try:
                con.execute("DELETE FROM events")
            finally:
                con.close()
        return True
    except Exception:
        return False