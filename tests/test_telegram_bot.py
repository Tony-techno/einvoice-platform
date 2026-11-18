import copy

from app import telegram_bot as tb
from app.extract_invoice import Invoice
from app.sample_data import GOOD_INVOICE
from app.validator import validate


def test_pass_reply():
    text = tb.format_reply(Invoice.model_validate(GOOD_INVOICE), [], "m")
    assert "PASS" in text and "INV-2026-0042" in text


def test_fail_reply_lists_rules():
    bad = copy.deepcopy(GOOD_INVOICE)
    bad["vat_amount"] = 300.0
    inv = Invoice.model_validate(bad)
    text = tb.format_reply(inv, validate(inv), "m")
    assert "FAIL" in text and "R10" in text


def test_photo_message_is_processed(monkeypatch):
    sent = []
    monkeypatch.setattr(tb, "send", lambda token, chat_id, text: sent.append(text))
    monkeypatch.setattr(tb, "download_file", lambda token, file_id: b"img")
    monkeypatch.setattr(
        tb, "extract_from_bytes",
        lambda data, mime: (Invoice.model_validate(GOOD_INVOICE), "fake-model"),
    )
    update = {"update_id": 1, "message": {"chat": {"id": 5}, "photo": [{"file_id": "a"}, {"file_id": "b"}]}}
    tb.handle_update("tok", update)
    assert any("PASS" in s for s in sent)


def test_text_message_gets_help(monkeypatch):
    sent = []
    monkeypatch.setattr(tb, "send", lambda token, chat_id, text: sent.append(text))
    tb.handle_update("tok", {"update_id": 2, "message": {"chat": {"id": 5}, "text": "hi"}})
    assert "photo" in sent[0].lower()