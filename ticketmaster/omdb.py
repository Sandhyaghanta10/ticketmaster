"""OMDb movie-details client (year, rating, plot, genre).

Fixes vs the original prototype: the API key comes from the OMDB_API_KEY environment variable
(never source code), requests use HTTPS with a timeout, failures become a clear OmdbError instead of
a crash, and results are cached so the UI doesn't hit the API on every click.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, Optional

OMDB_URL = "https://www.omdbapi.com/"


class OmdbError(Exception):
    """OMDb unreachable, returned garbage, or didn't know the movie."""


@dataclass(frozen=True)
class MovieInfo:
    year: str
    rated: str
    plot: str
    genre: str

    def summary(self) -> str:
        return f"{self.year}  |  {self.rated}  |  {self.genre}\n{self.plot}"


def http_get_json(url: str, params: Dict[str, str], timeout: float) -> dict:
    try:
        with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=timeout) as resp:
            return json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        raise OmdbError(f"Could not reach OMDb ({type(err).__name__})") from None  # never leak the URL (it holds the key)


class OmdbClient:
    def __init__(self, api_key: str, http_get: Callable[[str, Dict[str, str], float], dict] = http_get_json,
                 timeout: float = 5.0) -> None:
        self._api_key, self._http_get, self._timeout = api_key, http_get, timeout
        self._cache: Dict[str, MovieInfo] = {}

    @classmethod
    def from_env(cls) -> Optional["OmdbClient"]:
        """None when OMDB_API_KEY isn't set, so the app works (without details) instead of crashing."""
        key = os.environ.get("OMDB_API_KEY")
        return cls(key) if key else None

    def lookup(self, imdb_id: str) -> MovieInfo:
        if imdb_id in self._cache:
            return self._cache[imdb_id]
        data = self._http_get(OMDB_URL, {"i": imdb_id, "apikey": self._api_key}, self._timeout)
        if data.get("Response") == "False":
            raise OmdbError(data.get("Error", "Movie not found"))
        try:
            info = MovieInfo(data["Year"], data["Rated"], data["Plot"], data["Genre"])
        except KeyError as missing:
            raise OmdbError(f"OMDb response missing {missing.args[0]}") from None
        self._cache[imdb_id] = info
        return info
