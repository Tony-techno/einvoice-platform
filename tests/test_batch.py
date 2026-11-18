from app.batch import make_batch, process_batch, summarise


def test_same_day_gives_same_batch():
    assert make_batch("2026-11-18") == make_batch("2026-11-18")


def test_summary_adds_up():
    results, xml_files = process_batch(make_batch("2026-11-18"))
    summary = summarise(results)
    assert summary["total"] == 8
    assert summary["passed"] + summary["failed"] == 8
    assert summary["failed"] >= 1
    assert len(xml_files) == summary["passed"]