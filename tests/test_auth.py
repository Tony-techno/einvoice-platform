import pyotp
import pytest

from app import auth


@pytest.fixture(autouse=True)
def clean_failures():
    auth._failures.clear()
    yield
    auth._failures.clear()


def test_valid_code_is_accepted():
    secret = auth.new_secret()
    assert auth.verify_code(secret, pyotp.TOTP(secret).now()) is True


def test_wrong_code_is_rejected():
    secret = auth.new_secret()
    right = pyotp.TOTP(secret).now()
    wrong = f"{(int(right) + 1) % 1000000:06d}"
    assert auth.verify_code(secret, wrong) is False


def test_lockout_after_repeated_failures():
    secret = auth.new_secret()
    for _ in range(auth.MAX_FAILURES):
        auth.verify_code(secret, "abcdef")
    assert auth.is_locked() is True
    assert auth.verify_code(secret, pyotp.TOTP(secret).now()) is False


def test_lockout_expires():
    secret = auth.new_secret()
    start = 1_000_000.0
    for _ in range(auth.MAX_FAILURES):
        auth.verify_code(secret, "abcdef", now=start)
    assert auth.is_locked(now=start + 1) is True
    assert auth.is_locked(now=start + auth.WINDOW_SECONDS + 1) is False


def test_secret_is_cleaned_up(monkeypatch):
    monkeypatch.setenv("TOTP_SECRET", "abcd efgh")
    assert auth.get_secret() == "ABCDEFGH"
    monkeypatch.delenv("TOTP_SECRET")
    assert auth.get_secret() is None