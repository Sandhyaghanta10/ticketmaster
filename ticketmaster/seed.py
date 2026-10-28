"""Demo data so the app isn't empty on first launch."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .repository import MongoRepository

_DEMO = [("Interstellar", "Sci-Fi", 169), ("The Dark Knight", "Action", 152), ("Spirited Away", "Animation", 125)]


def seed_if_empty(repo: MongoRepository, now: Optional[datetime] = None) -> None:
    if repo.list_movies():
        return
    now = now or datetime.now()
    for i, (title, genre, minutes) in enumerate(_DEMO):
        movie = repo.add_movie(title, genre, minutes)
        for day in (1, 2):
            repo.add_show(movie.id, f"Screen {i + 1}", now + timedelta(days=day, hours=i),
                          rows=5, cols=8, price=250)
