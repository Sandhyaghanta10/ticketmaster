"""Plain data objects shared by the repository, service and GUI layers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

CONFIRMED = "confirmed"
CANCELLED = "cancelled"


@dataclass(frozen=True)
class Movie:
    id: str
    title: str
    genre: str
    duration_min: int


@dataclass(frozen=True)
class Show:
    id: str
    movie_id: str
    screen: str
    starts_at: datetime
    rows: int
    cols: int
    price: int  # rupees per seat
    booked: Tuple[str, ...] = ()

    @property
    def all_seats(self) -> Tuple[str, ...]:
        return tuple(f"{chr(ord('A') + r)}{c}" for r in range(self.rows)
                     for c in range(1, self.cols + 1))


@dataclass(frozen=True)
class Booking:
    id: str
    show_id: str
    customer: str
    seats: Tuple[str, ...]
    total: int
    status: str = CONFIRMED


class BookingError(Exception):
    """A business-rule violation (seat taken, show started, bad seat id, ...)."""
