"""MongoDB persistence. Takes any pymongo-compatible Database (real or mongomock).

Collections: movies, shows (with an embedded `booked` seat array), bookings.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from bson import ObjectId

from .models import CONFIRMED, Booking, Movie, Show


def _movie(doc: dict) -> Movie:
    return Movie(str(doc["_id"]), doc["title"], doc["genre"], doc["duration_min"],
                 doc.get("imdb_id", ""))


def _show(doc: dict) -> Show:
    return Show(str(doc["_id"]), doc["movie_id"], doc["screen"], doc["starts_at"],
                doc["rows"], doc["cols"], doc["price"], tuple(doc["booked"]))


def _booking(doc: dict) -> Booking:
    return Booking(str(doc["_id"]), doc["show_id"], doc["customer"],
                   tuple(doc["seats"]), doc["total"], doc["status"])


class MongoRepository:
    def __init__(self, db) -> None:
        self._movies, self._shows, self._bookings = db.movies, db.shows, db.bookings

    # --- movies & shows ----------------------------------------------------
    def add_movie(self, title: str, genre: str, duration_min: int, imdb_id: str = "") -> Movie:
        doc = {"title": title, "genre": genre, "duration_min": duration_min, "imdb_id": imdb_id}
        doc["_id"] = self._movies.insert_one(doc).inserted_id
        return _movie(doc)

    def list_movies(self) -> List[Movie]:
        return [_movie(d) for d in self._movies.find().sort("title", 1)]

    def add_show(self, movie_id: str, screen: str, starts_at: datetime,
                 rows: int, cols: int, price: int) -> Show:
        doc = {"movie_id": movie_id, "screen": screen, "starts_at": starts_at,
               "rows": rows, "cols": cols, "price": price, "booked": []}
        doc["_id"] = self._shows.insert_one(doc).inserted_id
        return _show(doc)

    def shows_for_movie(self, movie_id: str) -> List[Show]:
        return [_show(d) for d in self._shows.find({"movie_id": movie_id}).sort("starts_at", 1)]

    def get_show(self, show_id: str) -> Optional[Show]:
        doc = self._shows.find_one({"_id": ObjectId(show_id)})
        return _show(doc) if doc else None

    # --- seats -------------------------------------------------------------
    def try_reserve(self, show_id: str, seats: Sequence[str]) -> bool:
        """Atomically claim seats. One update_one = check ($nin) + claim ($push),
        so two buyers can never both win the same seat."""
        result = self._shows.update_one(
            {"_id": ObjectId(show_id), "booked": {"$nin": list(seats)}},
            {"$push": {"booked": {"$each": list(seats)}}})
        return result.modified_count == 1

    def release(self, show_id: str, seats: Sequence[str]) -> None:
        self._shows.update_one({"_id": ObjectId(show_id)},
                               {"$pull": {"booked": {"$in": list(seats)}}})

    # --- bookings ----------------------------------------------------------
    def add_booking(self, show_id: str, customer: str, seats: Sequence[str], total: int) -> Booking:
        doc = {"show_id": show_id, "customer": customer, "seats": list(seats),
               "total": total, "status": CONFIRMED}
        doc["_id"] = self._bookings.insert_one(doc).inserted_id
        return _booking(doc)

    def get_booking(self, booking_id: str) -> Optional[Booking]:
        doc = self._bookings.find_one({"_id": ObjectId(booking_id)})
        return _booking(doc) if doc else None

    def set_booking_status(self, booking_id: str, status: str) -> None:
        self._bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": status}})

    def bookings_for_customer(self, customer: str) -> List[Booking]:
        return [_booking(d) for d in self._bookings.find({"customer": customer})]
