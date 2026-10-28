"""Demo data so the app isn't empty on first launch."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .repository import MongoRepository

# Sample data: part of the November 2018 lineup from the original prototype.
# Run with `--as-of 2018-11-08` so these showtimes are still in the future.
_DEMO = [("Guardians of the Galaxy Vol. 2", "Action", 136, "tt3896198"),
         ("2.0", "Sci-Fi", 148, ""),
         ("Sarkar", "Drama", 162, "")]


def seed_if_empty(repo: MongoRepository, now: Optional[datetime] = None) -> None:
    if repo.list_movies():
        return
    now = now or datetime.now()
    for i, (title, genre, minutes, imdb_id) in enumerate(_DEMO):
        movie = repo.add_movie(title, genre, minutes, imdb_id)
        for day in (1, 2):
            repo.add_show(movie.id, f"Screen {i + 1}", now + timedelta(days=day, hours=i),
                          rows=5, cols=8, price=250)
