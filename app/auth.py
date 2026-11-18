import os
import time
from collections import deque

import pyotp

ISSUER = "E-Invoice Platform"
MAX_FAILURES = 5
WINDOW_SECONDS = 300

_failures = deque()


def new_secret() -> str:
    return pyotp.random_base32()


def get_secret():
    value = os.getenv("TOTP_SECRET", "").strip().replace(" ", "").upper()
    return value or None


def _prune(now: float) -> None:
    while _failures and now - _failures[0] > WINDOW_SECONDS:
        _failures.popleft()


def is_locked(now=None) -> bool:
    now = time.time() if now is None else now
    _prune(now)
    return len(_failures) >= MAX_FAILURES


def verify_code(secret: str, code: str, now=None) -> bool:
    """True if the 6-digit code is valid. Too many recent failures lock sign-in for a while."""
    now = time.time() if now is None else now
    if is_locked(now):
        return False
    code = (code or "").strip().replace(" ", "")
    ok = code.isdigit() and len(code) == 6 and pyotp.TOTP(secret).verify(code, valid_window=1)
    if not ok:
        _failures.append(now)
    return ok