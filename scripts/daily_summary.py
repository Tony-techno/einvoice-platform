import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.batch import make_batch, process_batch, render_report, summarise

now = datetime.now(timezone.utc)
day = now.strftime("%Y-%m-%d")

results, xml_files = process_batch(make_batch(day))
summary = summarise(results)

reports = ROOT / "reports"
reports.mkdir(exist_ok=True)

report = render_report(now.strftime("%Y-%m-%d %H:%M UTC"), summary, results, len(xml_files))
(reports / "daily_summary.md").write_text(report, encoding="utf-8")

# One row per day in a history file. Re-running on the same day replaces that day's row.
history = reports / "history.csv"
if history.exists():
    lines = history.read_text(encoding="utf-8").splitlines()
else:
    lines = ["date,total,passed,failed"]
lines = [line for line in lines if not line.startswith(day + ",")]
lines.append(f"{day},{summary['total']},{summary['passed']},{summary['failed']}")
history.write_text("\n".join(lines) + "\n", encoding="utf-8")

out = ROOT / "output"
out.mkdir(exist_ok=True)
for number, xml in xml_files.items():
    (out / f"{number}.xml").write_bytes(xml)

print(f"Processed {summary['total']} invoices: {summary['passed']} passed, {summary['failed']} failed.")
print(f"Wrote {len(xml_files)} XML files to output/ and the report to reports/.")