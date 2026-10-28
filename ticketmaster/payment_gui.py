"""Checkout window: summary + hold countdown info + bank choice -> pay -> ticket."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from .models import Booking, BookingError
from .service import BANKS, BookingService


class PaymentDialog(tk.Toplevel):
    """Modal. Closing the window without paying abandons the checkout and releases the seats."""

    def __init__(self, master: tk.Widget, service: BookingService, booking: Booking,
                 on_close: Callable[[Optional[Booking]], None]) -> None:
        super().__init__(master)
        self.title("Checkout")
        self._service, self._booking, self._on_close = service, booking, on_close
        self.bank = tk.StringVar(value=BANKS[0])

        body = ttk.Frame(self, padding=14)
        body.pack()
        ttk.Label(body, text=f"Seats: {', '.join(booking.seats)}\nTotal: Rs {booking.total}\n"
                             f"Your seats are held until {booking.expires_at:%H:%M:%S}.",
                  justify="left").pack(anchor="w", pady=(0, 8))
        ttk.Label(body, text="Pay with:").pack(anchor="w")
        for bank in BANKS:
            ttk.Radiobutton(body, text=bank, variable=self.bank, value=bank).pack(anchor="w")
        buttons = ttk.Frame(body)
        buttons.pack(pady=(10, 0))
        ttk.Button(buttons, text="Pay", command=self._pay).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self._abandon).pack(side="left", padx=4)
        self.protocol("WM_DELETE_WINDOW", self._abandon)
        self.transient(master)
        self.grab_set()

    def _pay(self) -> None:
        try:
            paid = self._service.pay(self._booking.id, self.bank.get())
        except BookingError as err:
            messagebox.showwarning("Payment failed", str(err), parent=self)
            return self._finish(None)  # hold expired or already gone: leave checkout
        messagebox.showinfo("Booked!", f"Ticket number: {paid.ticket_no}\nSeats: {', '.join(paid.seats)}\n"
                                       f"Paid: Rs {paid.total}\nPayment is simulated in this demo.", parent=self)
        self._finish(paid)

    def _abandon(self) -> None:
        try:
            self._service.cancel(self._booking.id)
        except BookingError:
            pass  # already expired/cancelled: nothing left to release
        self._finish(None)

    def _finish(self, booking: Optional[Booking]) -> None:
        self.destroy()
        self._on_close(booking)
