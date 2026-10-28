import pytest

from ticketmaster.omdb import OMDB_URL, MovieInfo, OmdbClient, OmdbError

GOOD = {"Response": "True", "Year": "2017", "Rated": "PG-13", "Plot": "Heroes bicker.", "Genre": "Action"}


class FakeHttp:
    def __init__(self, response):
        self.response, self.calls = response, []

    def __call__(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        return self.response


def test_lookup_parses_the_four_fields_and_sends_key_over_https():
    http = FakeHttp(GOOD)
    info = OmdbClient("KEY", http, timeout=3).lookup("tt1")
    assert info == MovieInfo("2017", "PG-13", "Heroes bicker.", "Action")
    assert http.calls == [(OMDB_URL, {"i": "tt1", "apikey": "KEY"}, 3)]
    assert OMDB_URL.startswith("https://")


def test_results_are_cached():
    http = FakeHttp(GOOD)
    client = OmdbClient("KEY", http)
    client.lookup("tt1")
    client.lookup("tt1")
    assert len(http.calls) == 1


def test_unknown_movie_and_incomplete_responses_raise_clear_errors():
    with pytest.raises(OmdbError, match="Incorrect IMDb ID"):
        OmdbClient("K", FakeHttp({"Response": "False", "Error": "Incorrect IMDb ID."})).lookup("bad")
    with pytest.raises(OmdbError, match="missing Plot"):
        OmdbClient("K", FakeHttp({"Response": "True", "Year": "1", "Rated": "R", "Genre": "x"})).lookup("tt2")


def test_failed_lookups_are_not_cached():
    responses = iter([{"Response": "False", "Error": "oops"}, GOOD])
    client = OmdbClient("K", lambda *_: next(responses))
    with pytest.raises(OmdbError):
        client.lookup("tt3")
    assert client.lookup("tt3").year == "2017"


def test_from_env(monkeypatch):
    monkeypatch.delenv("OMDB_API_KEY", raising=False)
    assert OmdbClient.from_env() is None  # app still works, just without details
    monkeypatch.setenv("OMDB_API_KEY", "abc")
    assert isinstance(OmdbClient.from_env(), OmdbClient)


def test_summary_text():
    assert "2017" in MovieInfo("2017", "PG-13", "Plot here", "Action").summary()


def test_network_errors_do_not_leak_the_api_key(monkeypatch):
    import urllib.error
    import urllib.request
    from ticketmaster.omdb import http_get_json

    def boom(*_args, **_kwargs):
        raise urllib.error.URLError("down")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(OmdbError) as err:
        http_get_json(OMDB_URL, {"i": "tt1", "apikey": "SECRETKEY"}, 1)
    assert "SECRETKEY" not in str(err.value) and "SECRETKEY" not in repr(err.value.__cause__)
