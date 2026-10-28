"""OTP verification for the demo login.

Replaces the original prototype's `random.randint(1000, 9999)` shown in a popup, which never expired,
could be guessed unlimited times, and used a non-cryptographic PRNG. Here the code is
  * generated with `secrets` (6 digits),
  * valid for `ttl_s` seconds,
  * limited to `max_attempts` wrong guesses,
  * single-use.
Delivery (SMS) is out of scope: `issue()` returns the code and the caller decides how to show it.
"""
from __future__ import annotations

import hmac
import re
import secrets
import time
from dataclasses import dataclass
from typing import Callable, Dict

_NAME = re.compile(r"^[A-Za-z][A-Za-z ]*$")
_MOBILE = re.compile(r"^[6-9]\d{9}$")  # Indian mobile numbers: 10 digits, start with 6-9


class OtpError(Exception):
    """Invalid input, or the OTP is wrong / expired / used up."""


@dataclass
class _Pending:
    code: str
    expires_at: float
    attempts_left: int


def _random_code() -> str:
    return f"{secrets.randbelow(10 ** 6):06d}"


class OtpService:
    def __init__(self, clock: Callable[[], float] = time.monotonic, ttl_s: float = 300.0,
                 max_attempts: int = 3, code_factory: Callable[[], str] = _random_code) -> None:
        self._clock, self._ttl, self._max_attempts = clock, ttl_s, max_attempts
        self._code_factory = code_factory
        self._pending: Dict[str, _Pending] = {}

    def issue(self, name: str, mobile: str) -> str:
        if not _NAME.match(name.strip()):
            raise OtpError("Name must contain letters only")
        if not _MOBILE.match(mobile):
            raise OtpError("Enter a valid 10-digit mobile number")
        code = self._code_factory()
        self._pending[mobile] = _Pending(code, self._clock() + self._ttl, self._max_attempts)
        return code

    def verify(self, mobile: str, code: str) -> None:
        """Returns normally on success; raises OtpError otherwise. A code works only once."""
        pending = self._pending.get(mobile)
        if pending is None:
            raise OtpError("Request an OTP first")
        if self._clock() >= pending.expires_at:
            del self._pending[mobile]
            raise OtpError("OTP expired - request a new one")
        if not hmac.compare_digest(pending.code, code.strip()):
            pending.attempts_left -= 1
            if pending.attempts_left <= 0:
                del self._pending[mobile]
                raise OtpError("Too many wrong attempts - request a new OTP")
            raise OtpError(f"Wrong OTP ({pending.attempts_left} attempts left)")
        del self._pending[mobile]
