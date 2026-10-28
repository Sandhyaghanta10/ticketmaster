# TicketMaster - Online Movie Ticket Booking (desktop)

Desktop app for browsing movies and booking seats, backed by MongoDB.

> Recreated in 2026. Originally built 2018–22.

## Features
- Browse movies and showtimes, pick seats from a live seat map (taken seats are disabled)
- Book up to 6 seats per booking; total price is calculated automatically
- Cancel a booking (seats are released) until the show starts
- Seed data on first launch so the app isn't empty

## The interesting bit: no double-booking
The classic ticketing bug is a read-then-write race: two buyers both see seat A1 as free, then both write it.
Here, reserving seats is **one atomic MongoDB update**:
```python
shows.update_one(
    {"_id": show_id, "booked": {"$nin": seats}},   # only if none of these seats is taken ...
    {"$push": {"booked": {"$each": seats}}})        # ... claim them all in the same operation
```
If `modified_count == 0`, someone else got there first and *none* of the requested seats are claimed
(all-or-nothing, covered by a test).

## Design
```
gui.py          Tkinter view, thin, no rules
service.py      Rules: validation, seat limits, show-started checks. Clock injected for tests
repository.py   All MongoDB access (takes any pymongo-compatible database)
models.py       Dataclasses + BookingError
```

## Run
```bash
uv venv && uv pip install pymongo pytest mongomock
.venv/bin/python -m pytest -q                 # 15 tests, uses an in-memory fake MongoDB

python -m ticketmaster --memory               # try the GUI with no database
docker run -d -p 27017:27017 mongo            # or use a real MongoDB ...
python -m ticketmaster                        # ... (override with MONGO_URI)
```
The GUI needs a Python build with working Tcl/Tk (macOS system Python or python.org builds).

## Limitations (honest list)
- Tests run against `mongomock`, which imitates MongoDB; the atomicity guarantee itself comes from real MongoDB's
  single-document atomic updates and is **not** exercised by a concurrent test here
- No payments, user accounts or seat-hold timeouts
- Seat availability in the UI is refreshed on each action, not pushed live

## Possible research-flavored extension
Benchmark this guard against a naive read-then-write version under N concurrent buyers on a real MongoDB,
and measure the double-booking rate and throughput of each.
