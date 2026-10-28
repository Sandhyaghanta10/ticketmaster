"""Tkinter login screen: name + mobile -> OTP -> on_success(name)."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .otp import OtpError, OtpService


class LoginFrame(ttk.Frame):
    def __init__(self, master: tk.Tk, otp: OtpService, on_success: Callable[[str], None]) -> None:
        super().__init__(master, padding=20)
        self._otp, self._on_success = otp, on_success
        self.name, self.mobile, self.code = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for row, (label, var) in enumerate((("Name", self.name), ("Mobile number", self.mobile))):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=4)
            ttk.Entry(self, textvariable=var, width=28).grid(row=row, column=1)
        ttk.Button(self, text="Send OTP", command=self._send).grid(row=2, column=1, sticky="w", pady=4)
        ttk.Label(self, text="OTP").grid(row=3, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(self, textvariable=self.code, width=12).grid(row=3, column=1, sticky="w")
        ttk.Button(self, text="Verify & continue", command=self._verify).grid(row=4, column=1, sticky="w", pady=4)
        self.pack()

    def _send(self) -> None:
        try:
            code = self._otp.issue(self.name.get(), self.mobile.get())
        except OtpError as err:
            return messagebox.showwarning("Cannot send OTP", str(err))
        # Demo mode: a real deployment would hand `code` to an SMS gateway instead.
        messagebox.showinfo("Demo OTP", f"Your OTP is {code}\n(shown on screen because this is a demo; no SMS is sent)")

    def _verify(self) -> None:
        try:
            self._otp.verify(self.mobile.get(), self.code.get())
        except OtpError as err:
            return messagebox.showwarning("Verification failed", str(err))
        self._on_success(self.name.get().strip())
