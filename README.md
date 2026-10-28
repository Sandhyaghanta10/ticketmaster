# Movizoo (TicketMaster) - Online Movie Ticket Booking (desktop)

> Recreated in 2026. Originally built 2018–22.

Desktop app for browsing movies, verifying with an OTP, picking seats and booking, backed by MongoDB.

## Features
- OTP login (name + 10-digit mobile); OTP is shown on screen in demo mode, no SMS is sent
- Browse movies and showtimes, with year / rating / genre / plot fetched from the OMDb API
- Live seat map (taken seats are disabled); up to 6 seats per booking; total computed from the selected seats
- Cancel a booking (seats are released) until the show starts

## From prototype to refactor
The original 2018 prototype is kept in [`legacy/movizoo_original.py`](./legacy/movizoo_original.py)
(formatting restored, OMDb key removed, logic untouched). It was a single ~150-line script built on global state.
This version keeps the idea and fixes what was wrong with it:

| Original prototype | This version |
|---|---|
| OMDb API key hardcoded in source | Key read from `OMDB_API_KEY`; the client never puts the key in an error message (tested) |
| Price: `+120` on **every click**, so unchecking a seat still raised the price | Total = seat price x number of distinct selected seats |
| OTP: 4-digit `random.randint`, never expired, unlimited guesses | `secrets`, 6 digits, 5-minute expiry, 3 attempts, single-use (tested) |
| No persistence; nothing stopped two people booking the same seat | MongoDB with an atomic seat reservation (below) |
| HTTP, no timeout, any API failure crashed the app | HTTPS, 5 s timeout, results cached, failures shown as a message |
| A new `Tk()` root window for every screen | One window, frames swapped in and out |
| Logic and UI tangled together; untested | Layers: `service` / `repository` / `otp` / `omdb` / GUI; 34 unit tests |

Note: the original kept all state in memory and had **no database**. MongoDB was added in this version.

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
gui.py / login_gui.py   Tkinter views, thin, no rules
service.py              Booking rules: validation, seat limits, show-started checks (clock injected)
otp.py                  OTP issue/verify (expiry, attempt limit, single-use)
omdb.py                 OMDb client (env key, HTTPS, timeout, cache)
repository.py           All MongoDB access (takes any pymongo-compatible database)
models.py               Dataclasses + BookingError
legacy/                 The original prototype, for reference only
```

## Run
```bash
uv venv && uv pip install pymongo pytest mongomock
.venv/bin/python -m pytest -q                 # 34 tests, in-memory fake MongoDB, no network

export OMDB_API_KEY=...                       # optional: free key from omdbapi.com; no key = no movie details
python -m ticketmaster --memory               # try the GUI with no database
docker run -d -p 27017:27017 mongo            # or use a real MongoDB (override with MONGO_URI)
python -m ticketmaster
```
The GUI needs a Python build with working Tcl/Tk (macOS system Python or python.org builds).

## Limitations (honest list)
- Tests run against `mongomock`, which imitates MongoDB; the atomicity guarantee itself comes from real MongoDB's
  single-document atomic updates and is **not** exercised by a concurrent test here
- OTP delivery is simulated (shown on screen); there is no SMS gateway, payments, or seat-hold timeout
- OMDb lookups run on the UI thread (bounded by the 5 s timeout); a worker thread would be the next step
- The GUI modules are import-tested only; I have not built the window or click-tested it end to end

## Possible research-flavored extension
Benchmark the atomic guard against a naive read-then-write version under N concurrent buyers on a real MongoDB,
and measure the double-booking rate and throughput of each.
