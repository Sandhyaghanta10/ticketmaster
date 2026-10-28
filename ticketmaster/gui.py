"""Tkinter front-end. Thin on purpose: all rules live in BookingService."""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable, Dict, Optional, Set

from .login_gui import LoginFrame
from .models import Booking, BookingError, Movie, Show
from .omdb import OmdbClient, OmdbError
from .otp import OtpService
from .payment_gui import PaymentDialog
from .repository import MongoRepository
from .service import BookingService


class TicketMasterApp(ttk.Frame):
    def __init__(self, master: tk.Tk, repo: MongoRepository, service: BookingService,
                 customer: str = "", omdb: Optional[OmdbClient] = None) -> None:
        super().__init__(master, padding=10)
        self.repo, self.service, self.customer, self.omdb = repo, service, customer, omdb
        self.movies = repo.list_movies()
        self.shows: list = []
        self.show: Optional[Show] = None
        self.selected: Set[str] = set()
        self.seat_buttons: Dict[str, tk.Button] = {}
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="Movies").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Showtimes").grid(row=0, column=1, sticky="w")
        self.movie_list = tk.Listbox(self, width=28, height=8, exportselection=False)
        self.show_list = tk.Listbox(self, width=34, height=8, exportselection=False)
        self.movie_list.grid(row=1, column=0, padx=4)
        self.show_list.grid(row=1, column=1, padx=4)
        for m in self.movies:
            self.movie_list.insert("end", f"{m.title} ({m.genre}, {m.duration_min} min)")
        self.movie_list.bind("<<ListboxSelect>>", self._pick_movie)
        self.show_list.bind("<<ListboxSelect>>", self._pick_show)

        self.grid_frame = ttk.Frame(self)
        self.grid_frame.grid(row=2, column=0, columnspan=2, pady=10)
        self.name = tk.StringVar(value=self.customer)
        ttk.Label(self, text="Your name").grid(row=3, column=0, sticky="e")
        ttk.Entry(self, textvariable=self.name, width=24).grid(row=3, column=1, sticky="w")
        ttk.Button(self, text="Proceed to payment", command=self._checkout).grid(row=4, column=1, sticky="w", pady=6)
        self.status = ttk.Label(self, text="Pick a movie, then a showtime.")
        self.status.grid(row=5, column=0, columnspan=2, sticky="w")
        self.details = ttk.Label(self, wraplength=520, justify="left")
        self.details.grid(row=6, column=0, columnspan=2, sticky="w", pady=4)

    def _pick_movie(self, _event=None) -> None:
        index = self.movie_list.curselection()
        if not index:
            return
        self.shows = self.repo.shows_for_movie(self.movies[index[0]].id)
        self._show_details(self.movies[index[0]])
        self.show_list.delete(0, "end")
        for s in self.shows:
            self.show_list.insert("end", f"{s.starts_at:%d %b %H:%M} - {s.screen} - Rs {s.price}")

    def _show_details(self, movie: Movie) -> None:
        if self.omdb is None or not movie.imdb_id:
            self.details.config(text="")
            return
        try:  # blocks the UI up to the client timeout; fine for a demo, a thread would be next
            self.details.config(text=self.omdb.lookup(movie.imdb_id).summary())
        except OmdbError as err:
            self.details.config(text=f"Details unavailable: {err}")

    def _pick_show(self, _event=None) -> None:
        index = self.show_list.curselection()
        if index:
            self._render_seats(self.shows[index[0]].id)

    def _render_seats(self, show_id: str) -> None:
        self.service.release_expired_holds()  # abandoned checkouts free their seats
        self.show = self.repo.get_show(show_id)  # fresh copy so we see other buyers' seats
        self.selected.clear()
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.seat_buttons = {}
        for i, seat in enumerate(self.show.all_seats):
            taken = seat in self.show.booked
            btn = tk.Button(self.grid_frame, text=seat, width=4,
                            state="disabled" if taken else "normal",
                            bg="#c0392b" if taken else "#ecf0f1",
                            command=lambda s=seat: self._toggle(s))
            btn.grid(row=i // self.show.cols, column=i % self.show.cols, padx=1, pady=1)
            self.seat_buttons[seat] = btn

    def _toggle(self, seat: str) -> None:
        self.selected ^= {seat}
        self.seat_buttons[seat].config(bg="#27ae60" if seat in self.selected else "#ecf0f1")

    def _checkout(self) -> None:
        """Hold the selected seats, then open the payment window."""
        if self.show is None:
            return messagebox.showwarning("Pick a show", "Choose a showtime first.")
        try:
            booking = self.service.hold(self.show.id, self.name.get(), self.selected)
        except BookingError as err:
            messagebox.showwarning("Cannot book", str(err))
            return self._render_seats(self.show.id)  # seats may have just been taken
        self._render_seats(self.show.id)  # show our held seats as taken
        PaymentDialog(self, self.service, booking, on_close=self._checkout_done)

    def _checkout_done(self, paid: Optional[Booking]) -> None:
        if paid:
            self.status.config(text=f"Ticket {paid.ticket_no}: {', '.join(paid.seats)}  (Rs {paid.total})")
        self._render_seats(self.show.id)


def main(repo: MongoRepository, now: Callable[[], datetime] = datetime.now) -> None:
    root = tk.Tk()
    root.title("MOVIZOO")
    service, omdb = BookingService(repo, now), OmdbClient.from_env()

    def start(customer: str) -> None:
        login.destroy()
        TicketMasterApp(root, repo, service, customer, omdb)

    login = LoginFrame(root, OtpService(), start)
    root.mainloop()
