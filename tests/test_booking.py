from datetime import datetime, timedelta

import mongomock
import pytest

from ticketmaster.models import CANCELLED, BookingError
from ticketmaster.repository import MongoRepository
from ticketmaster.service import MAX_SEATS_PER_BOOKING, BookingService

NOW = datetime(2026, 6, 1, 18, 0)


class Clock:
    def __init__(self):
        self.now = NOW

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def repo():
    return MongoRepository(mongomock.MongoClient().ticketmaster_test)


@pytest.fixture
def service(repo, clock):
    return BookingService(repo, clock)


@pytest.fixture
def show(repo):
    movie = repo.add_movie("Interstellar", "Sci-Fi", 169)
    return repo.add_show(movie.id, "Screen 1", NOW + timedelta(hours=3), rows=3, cols=4, price=200)


def test_seat_grid_is_rows_by_cols(show):
    assert len(show.all_seats) == 12
    assert show.all_seats[0] == "A1" and show.all_seats[-1] == "C4"


def test_booking_computes_total_and_marks_seats_taken(service, repo, show):
    booking = service.book(show.id, "Asha", ["A2", "A1"])
    assert booking.total == 400 and booking.seats == ("A1", "A2")
    assert repo.get_show(show.id).booked == ("A1", "A2")


def test_double_booking_is_rejected_and_leaves_state_untouched(service, repo, show):
    service.book(show.id, "Asha", ["A1", "A2"])
    with pytest.raises(BookingError, match="just taken"):
        service.book(show.id, "Ravi", ["A2", "A3"])  # A2 clash -> A3 must NOT be claimed
    assert repo.get_show(show.id).booked == ("A1", "A2")


def test_duplicate_seats_in_one_request_are_collapsed(service, show):
    assert service.book(show.id, "Asha", ["B1", "B1"]).total == 200


@pytest.mark.parametrize("seats,msg", [
    ([], "at least one"),
    (["Z9"], "Invalid seat"),
    (["A5"], "Invalid seat"),  # only 4 columns
    ([f"A{i}" for i in range(1, 4)] + ["B1", "B2", "B3", "B4"], "At most"),
])
def test_invalid_requests(service, show, seats, msg):
    assert MAX_SEATS_PER_BOOKING == 6
    with pytest.raises(BookingError, match=msg):
        service.book(show.id, "Asha", seats)


def test_customer_name_required(service, show):
    with pytest.raises(BookingError, match="name"):
        service.book(show.id, "   ", ["A1"])


def test_cannot_book_after_show_started(service, clock, show):
    clock.now = show.starts_at
    with pytest.raises(BookingError, match="already started"):
        service.book(show.id, "Asha", ["A1"])


def test_cancel_frees_seats_for_someone_else(service, repo, show):
    booking = service.book(show.id, "Asha", ["A1"])
    assert service.cancel(booking.id).status == CANCELLED
    assert repo.get_show(show.id).booked == ()
    assert service.book(show.id, "Ravi", ["A1"]).seats == ("A1",)


def test_cannot_cancel_twice_or_after_start(service, clock, show):
    booking = service.book(show.id, "Asha", ["A1"])
    service.cancel(booking.id)
    with pytest.raises(BookingError, match="already cancelled"):
        service.cancel(booking.id)
    other = service.book(show.id, "Ravi", ["B1"])
    clock.now = show.starts_at + timedelta(minutes=1)
    with pytest.raises(BookingError, match="after the show"):
        service.cancel(other.id)


def test_unknown_show_and_booking(service):
    unknown = "0" * 24
    with pytest.raises(BookingError, match="Unknown show"):
        service.book(unknown, "Asha", ["A1"])
    with pytest.raises(BookingError, match="Unknown booking"):
        service.cancel(unknown)
