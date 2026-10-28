"""Booking rules, TicketMaster-style: HOLD seats -> PAY -> ticket.

  hold()   validates, atomically claims the seats, and starts a 5-minute checkout timer
  pay()    confirms the hold and issues a ticket number (payment itself is simulated)
  cancel() releases the seats (pending: any time; paid: until the show starts)
Holds nobody pays for are released automatically, so abandoned checkouts can't lock seats forever.
The clock is injected so tests control 'now'.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from typing import Callable, Iterable

from .models import CANCELLED, CONFIRMED, EXPIRED, PENDING, Booking, BookingError
from .repository import MongoRepository

MAX_SEATS_PER_BOOKING = 6
HOLD_MINUTES = 5
BANKS = ("SBI Bank", "ICICI Bank", "Bank of Baroda", "Modern Bank",
         "Central Bank of India", "Axis Bank", "Swiss Bank")  # the banks from the original prototype


def new_ticket_no() -> str:
    return "MZ-" + uuid.uuid4().hex[:8].upper()


class BookingService:
    def __init__(self, repo: MongoRepository, now: Callable[[], datetime] = datetime.now,
                 ticket_factory: Callable[[], str] = new_ticket_no) -> None:
        self._repo, self._now, self._ticket_factory = repo, now, ticket_factory

    def release_expired_holds(self) -> int:
        """Free the seats of every unpaid hold whose timer ran out. Returns how many were released."""
        expired = self._repo.expired_holds(self._now())
        for booking in expired:
            self._expire(booking)
        return len(expired)

    def hold(self, show_id: str, customer: str, seats: Iterable[str]) -> Booking:
        self.release_expired_holds()
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
        expires_at = self._now() + timedelta(minutes=HOLD_MINUTES)
        return self._repo.add_booking(show_id, customer, chosen, show.price * len(chosen), expires_at)

    def pay(self, booking_id: str, bank: str) -> Booking:
        booking = self._get(booking_id)
        if booking.status == CONFIRMED:
            raise BookingError("Already paid")
        if booking.status != PENDING:
            raise BookingError(f"This booking is {booking.status}; please pick seats again")
        if booking.expires_at <= self._now():
            self._expire(booking)
            raise BookingError("Your seat hold expired - please pick seats again")
        if bank not in BANKS:
            raise BookingError("Choose a bank")
        self._repo.confirm_booking(booking_id, self._ticket_factory(), bank)
        return self._get(booking_id)

    def cancel(self, booking_id: str) -> Booking:
        booking = self._get(booking_id)
        if booking.status not in (PENDING, CONFIRMED):
            raise BookingError(f"Booking is already {booking.status}")
        if booking.status == CONFIRMED and self._repo.get_show(booking.show_id).starts_at <= self._now():
            raise BookingError("Cannot cancel after the show has started")
        self._repo.release(booking.show_id, booking.seats)
        self._repo.set_booking_status(booking_id, CANCELLED)
        return self._get(booking_id)

    def _get(self, booking_id: str) -> Booking:
        booking = self._repo.get_booking(booking_id)
        if booking is None:
            raise BookingError("Unknown booking")
        return booking

    def _expire(self, booking: Booking) -> None:
        self._repo.release(booking.show_id, booking.seats)
        self._repo.set_booking_status(booking.id, EXPIRED)
