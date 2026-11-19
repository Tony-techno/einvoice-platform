import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.emailer import build_message, send_message

sender = os.getenv("GMAIL_ADDRESS", "").strip()
password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
recipient = os.getenv("REPORT_RECIPIENT", "").strip() or sender

if not sender or not password:
    print("Email is not configured (GMAIL_ADDRESS or GMAIL_APP_PASSWORD is missing). Skipping.")
    raise SystemExit(0)

report = ROOT / "reports" / "daily_summary.md"
if not report.exists():
    raise SystemExit("No report found at reports/daily_summary.md.")

day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
message = build_message(
    sender, recipient, f"Daily invoice summary {day}", report.read_text(encoding="utf-8")
)

try:
    send_message(message, password)
except Exception as e:
    # Print only the error type. Never print addresses or passwords: logs on a public repo are public.
    raise SystemExit(f"Could not send the email ({type(e).__name__}).")

print("Summary email sent.")