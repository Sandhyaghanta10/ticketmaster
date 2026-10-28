from datetime import date, datetime

import mongomock

from ticketmaster.clock import clock_for
from ticketmaster.repository import MongoRepository
from ticketmaster.seed import seed_if_empty

AS_OF = datetime(2018, 11, 8, 10, 0)


def test_seed_populates_once_and_is_idempotent():
    repo = MongoRepository(mongomock.MongoClient().seed_test)
    seed_if_empty(repo, AS_OF)
    seed_if_empty(repo, AS_OF)  # second call must not duplicate
    movies = repo.list_movies()
    assert sorted(m.title for m in movies) == ["2.0", "Guardians of the Galaxy Vol. 2", "Sarkar"]
    assert any(m.imdb_id == "tt3896198" for m in movies)
    assert all(len(repo.shows_for_movie(m.id)) == 2 for m in movies)


def test_seeded_showtimes_are_in_the_future_of_the_as_of_date():
    repo = MongoRepository(mongomock.MongoClient().seed_test2)
    seed_if_empty(repo, AS_OF)
    shows = [s for m in repo.list_movies() for s in repo.shows_for_movie(m.id)]
    assert shows and all(s.starts_at > AS_OF and s.starts_at.year == 2018 for s in shows)


def test_as_of_clock_is_frozen_at_ten_am_and_default_is_real_time():
    now = clock_for(date(2018, 11, 8))
    assert now() == datetime(2018, 11, 8, 10, 0) and now() == now()
    assert abs((clock_for()() - datetime.now()).total_seconds()) < 5


def test_gui_modules_import():
    import ticketmaster.gui  # noqa: F401  (catches typos / bad imports without needing a display)
    import ticketmaster.login_gui  # noqa: F401
    import ticketmaster.payment_gui  # noqa: F401
