from app import emailer


def test_message_fields():
    msg = emailer.build_message("a@example.com", "b@example.com", "Subject", "Body text")
    assert msg["From"] == "a@example.com"
    assert msg["To"] == "b@example.com"
    assert msg["Subject"] == "Subject"
    assert "Body text" in msg.get_content()


def test_send_uses_ssl_and_logs_in(monkeypatch):
    calls = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            calls["server"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, user, password):
            calls["login"] = (user, password)

        def send_message(self, msg):
            calls["subject"] = msg["Subject"]

    monkeypatch.setattr(emailer.smtplib, "SMTP_SSL", FakeSMTP)
    msg = emailer.build_message("a@example.com", "b@example.com", "Hello", "Body")
    emailer.send_message(msg, "secret")

    assert calls["server"] == ("smtp.gmail.com", 465)
    assert calls["login"] == ("a@example.com", "secret")
    assert calls["subject"] == "Hello"