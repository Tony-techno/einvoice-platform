import copy

from app import db
from app.sample_data import GOOD_INVOICE


def test_logging_and_stats(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.duckdb"))

    bad = copy.deepcopy(GOOD_INVOICE)
    bad["vat_amount"] = 300.0

    assert db.log_event("sample_loaded", GOOD_INVOICE) is True
    assert db.log_event("sample_loaded", bad) is True

    stats = db.get_stats()
    assert stats["total"] == 2
    assert stats["passed"] == 1
    assert stats["failed"] == 1
    assert {row["Rule"] for row in stats["top_rules"]} == {"R10", "R11"}


def test_bad_input_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.duckdb"))
    assert db.log_event("sample_loaded", {"not": "an invoice"}) is False