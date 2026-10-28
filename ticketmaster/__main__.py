"""Entry point:  python -m ticketmaster [--memory]"""
from __future__ import annotations

import argparse
import os
import sys

from .repository import MongoRepository
from .seed import seed_if_empty


def connect(in_memory: bool):
    if in_memory:
        import mongomock  # dev-only dependency; lets you try the app without MongoDB
        return mongomock.MongoClient().ticketmaster
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError
    client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"),
                         serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError:
        sys.exit("Cannot reach MongoDB. Start one (docker run -p 27017:27017 mongo), "
                 "set MONGO_URI, or run with --memory.")
    return client.ticketmaster


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", action="store_true", help="use an in-memory fake MongoDB")
    args = parser.parse_args()
    repo = MongoRepository(connect(args.memory))
    seed_if_empty(repo)
    from .gui import main  # imported late so --help works without Tk
    main(repo)


run()
