from datetime import datetime

import mongomock

from ticketmaster.repository import MongoRepository
from ticketmaster.seed import seed_if_empty


def test_seed_populates_once_and_is_idempotent():
    repo = MongoRepository(mongomock.MongoClient().seed_test)
    seed_if_empty(repo, datetime(2026, 6, 1))
    seed_if_empty(repo, datetime(2026, 6, 1))  # second call must not duplicate
    movies = repo.list_movies()
    assert len(movies) == 3
    assert all(len(repo.shows_for_movie(m.id)) == 2 for m in movies)


def test_gui_module_imports():
    import ticketmaster.gui  # noqa: F401  (catches typos / bad imports without needing a display)
