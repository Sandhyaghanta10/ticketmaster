"""Booking rules. The clock is injected so tests control 'now'."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Callable, Iterable

from .models import CANCELLED, CONFIRMED, Booking, BookingError
from .repository import MongoRepository

MAX_SEATS_PER_BOOKING = 6
_SEAT = re.compile(r"^([A-Z])(\d+)$")


class BookingService:
    def __init__(self, repo: MongoRepository, now: Callable[[], datetime] = datetime.now) -> None:
        self._repo, self._now = repo, now

    def book(self, show_id: str, customer: str, seats: Iterable[str]) -> Booking:
        show = self._repo.get_show(show_id)
        if show is None:
            raise BookingError("Unknown show")
        if show.starts_at <= self._now():
            raise BookingError("This show has already started")
        customer = customer.strip()
        if not customer:
            raise BookingError("Customer name is required")
        chosen = sorted(set(seats))
        if not chosen:
            raise BookingError("Pick at least one seat")
        if len(chosen) > MAX_SEATS_PER_BOOKING:
            raise BookingError(f"At most {MAX_SEATS_PER_BOOKING} seats per booking")
        invalid = [s for s in chosen if s not in show.all_seats]
        if invalid:
            raise BookingError(f"Invalid seat(s): {', '.join(invalid)}")
        if not self._repo.try_reserve(show_id, chosen):
            raise BookingError("One or more of those seats were just taken")
        return self._repo.add_booking(show_id, customer, chosen, show.price * len(chosen))

    def cancel(self, booking_id: str) -> Booking:
        booking = self._repo.get_booking(booking_id)
        if booking is None:
            raise BookingError("Unknown booking")
        if booking.status != CONFIRMED:
            raise BookingError("Booking is already cancelled")
        show = self._repo.get_show(booking.show_id)
        if show.starts_at <= self._now():
            raise BookingError("Cannot cancel after the show has started")
        self._repo.release(booking.show_id, booking.seats)
        self._repo.set_booking_status(booking_id, CANCELLED)
        return self._repo.get_booking(booking_id)
