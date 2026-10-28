"""Booking-rule tests, run against three dates between 2018 and 2023.

The dates are chosen to hit calendar edge cases: an ordinary 2018 evening, a late-night show that
rolls over the 2020 leap day, and a New Year's Eve show that ends up in 2024.
"""
from datetime import datetime, timedelta

import mongomock
import pytest

from ticketmaster.models import CANCELLED, CONFIRMED, EXPIRED, PENDING, BookingError
from ticketmaster.repository import MongoRepository
from ticketmaster.service import BANKS, HOLD_MINUTES, MAX_SEATS_PER_BOOKING, BookingService

DATES = [datetime(2018, 11, 8, 18, 0),    # ordinary evening
         datetime(2020, 2, 28, 21, 30),   # show starts after midnight on 29 Feb (leap day)
         datetime(2023, 12, 31, 22, 0)]   # show starts in 2024


class Clock:
    def __init__(self, start):
        self.now = start

    def __call__(self):
        return self.now


@pytest.fixture(params=DATES, ids=lambda d: d.date().isoformat())
def clock(request):
    return Clock(request.param)


@pytest.fixture
def repo():
    return MongoRepository(mongomock.MongoClient().ticketmaster_test)


@pytest.fixture
def service(repo, clock):
    return BookingService(repo, clock)


@pytest.fixture
def show(repo, clock):
    movie = repo.add_movie("Guardians of the Galaxy Vol. 2", "Action", 136, "tt3896198")
    return repo.add_show(movie.id, "Screen 1", clock.now + timedelta(hours=3), rows=3, cols=4, price=120)


def buy(service, show_id, customer, seats, bank=BANKS[0]):
    return service.pay(service.hold(show_id, customer, seats).id, bank)


# --- seat map / hold -------------------------------------------------------
def test_seat_grid_is_rows_by_cols(show):
    assert len(show.all_seats) == 12
    assert show.all_seats[0] == "A1" and show.all_seats[-1] == "C4"


def test_hold_computes_total_claims_seats_and_starts_the_timer(service, repo, show, clock):
    booking = service.hold(show.id, "Asha", ["A2", "A1"])
    assert (booking.status, booking.seats, booking.total) == (PENDING, ("A1", "A2"), 240)
    assert booking.expires_at == clock.now + timedelta(minutes=HOLD_MINUTES)
    assert repo.get_show(show.id).booked == ("A1", "A2")


def test_double_booking_is_rejected_and_leaves_state_untouched(service, repo, show):
    service.hold(show.id, "Asha", ["A1", "A2"])
    with pytest.raises(BookingError, match="just taken"):
        service.hold(show.id, "Ravi", ["A2", "A3"])  # A2 clashes -> A3 must NOT be claimed
    assert repo.get_show(show.id).booked == ("A1", "A2")


def test_duplicate_seats_in_one_request_are_collapsed(service, show):
    assert service.hold(show.id, "Asha", ["B1", "B1"]).total == 120


@pytest.mark.parametrize("seats,msg", [
    ([], "at least one"),
    (["Z9"], "Invalid seat"),
    (["A5"], "Invalid seat"),  # only 4 columns
    ([f"A{i}" for i in range(1, 4)] + ["B1", "B2", "B3", "B4"], "At most"),
])
def test_invalid_requests(service, show, seats, msg):
    assert MAX_SEATS_PER_BOOKING == 6
    with pytest.raises(BookingError, match=msg):
        service.hold(show.id, "Asha", seats)


def test_customer_name_required(service, show):
    with pytest.raises(BookingError, match="name"):
        service.hold(show.id, "   ", ["A1"])


def test_cannot_hold_after_show_started(service, clock, show):
    clock.now = show.starts_at
    with pytest.raises(BookingError, match="already started"):
        service.hold(show.id, "Asha", ["A1"])


# --- pay -------------------------------------------------------------------
def test_pay_confirms_and_issues_a_ticket(service, repo, show):
    booking = buy(service, show.id, "Asha", ["A1"], bank="Axis Bank")
    assert booking.status == CONFIRMED and booking.ticket_no.startswith("MZ-")
    assert repo.get_show(show.id).booked == ("A1",)  # seats stay taken


def test_cannot_pay_twice_or_with_unknown_bank(service, show):
    held = service.hold(show.id, "Asha", ["A1"])
    with pytest.raises(BookingError, match="Choose a bank"):
        service.pay(held.id, "Bank of Nowhere")
    service.pay(held.id, BANKS[1])
    with pytest.raises(BookingError, match="Already paid"):
        service.pay(held.id, BANKS[1])


def test_ticket_numbers_are_unique(service, show):
    tickets = {buy(service, show.id, "Asha", [seat]).ticket_no for seat in ("A1", "A2", "A3", "B1")}
    assert len(tickets) == 4


def test_paying_after_the_hold_expires_fails_and_frees_the_seats(service, repo, show, clock):
    held = service.hold(show.id, "Asha", ["A1"])
    clock.now += timedelta(minutes=HOLD_MINUTES)
    with pytest.raises(BookingError, match="hold expired"):
        service.pay(held.id, BANKS[0])
    assert repo.get_show(show.id).booked == ()
    assert repo.get_booking(held.id).status == EXPIRED


def test_pay_just_before_expiry_still_works(service, show, clock):
    held = service.hold(show.id, "Asha", ["A1"])
    clock.now += timedelta(minutes=HOLD_MINUTES) - timedelta(seconds=1)
    assert service.pay(held.id, BANKS[0]).status == CONFIRMED


def test_abandoned_hold_is_released_when_someone_else_tries_those_seats(service, repo, show, clock):
    abandoned = service.hold(show.id, "Asha", ["A1"])
    with pytest.raises(BookingError, match="just taken"):
        service.hold(show.id, "Ravi", ["A1"])  # still held
    clock.now += timedelta(minutes=HOLD_MINUTES)
    assert service.hold(show.id, "Ravi", ["A1"]).seats == ("A1",)  # timer ran out -> free again
    assert repo.get_booking(abandoned.id).status == EXPIRED


def test_paid_bookings_never_expire(service, repo, show, clock):
    booking = buy(service, show.id, "Asha", ["A1"])
    clock.now += timedelta(minutes=HOLD_MINUTES * 10)
    assert service.release_expired_holds() == 0
    assert repo.get_booking(booking.id).status == CONFIRMED


# --- cancel ----------------------------------------------------------------
def test_cancelling_a_pending_hold_frees_the_seats(service, repo, show):
    held = service.hold(show.id, "Asha", ["A1"])
    assert service.cancel(held.id).status == CANCELLED
    assert repo.get_show(show.id).booked == ()


def test_cancel_paid_booking_frees_seats_for_someone_else(service, repo, show):
    booking = buy(service, show.id, "Asha", ["A1"])
    assert service.cancel(booking.id).status == CANCELLED
    assert buy(service, show.id, "Ravi", ["A1"]).seats == ("A1",)


def test_cannot_cancel_twice_or_after_start(service, clock, show):
    booking = buy(service, show.id, "Asha", ["A1"])
    service.cancel(booking.id)
    with pytest.raises(BookingError, match="already cancelled"):
        service.cancel(booking.id)
    other = buy(service, show.id, "Ravi", ["B1"])
    clock.now = show.starts_at + timedelta(minutes=1)
    with pytest.raises(BookingError, match="after the show"):
        service.cancel(other.id)


def test_unknown_show_and_booking(service):
    unknown = "0" * 24
    with pytest.raises(BookingError, match="Unknown show"):
        service.hold(unknown, "Asha", ["A1"])
    with pytest.raises(BookingError, match="Unknown booking"):
        service.cancel(unknown)
    with pytest.raises(BookingError, match="Unknown booking"):
        service.pay(unknown, BANKS[0])
