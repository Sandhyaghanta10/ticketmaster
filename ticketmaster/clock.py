"""Clock selection: real time, or a frozen 'as-of' date for demos with historical sample data."""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Callable, Optional


def clock_for(as_of: Optional[date] = None) -> Callable[[], datetime]:
    """Real time by default; with `as_of` the app 'lives' on that date at 10:00 (frozen)."""
    if as_of is None:
        return datetime.now
    frozen = datetime.combine(as_of, time(10, 0))
    return lambda: frozen
