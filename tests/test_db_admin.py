from app import db, db_admin
from app.sample_data import GOOD_INVOICE


def test_export_and_clear(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.duckdb"))
    db.log_event("sample_loaded", GOOD_INVOICE)
    assert "INV-2026-0042" in db_admin.export_csv()
    assert db_admin.clear_events() is True
    assert db.get_stats()["total"] == 0