import re
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from language_manager import N_, lang_mgr

from . import vars
from .dialog import Dialog

# Forward declaration for IDE/Linter support
if TYPE_CHECKING:

    def _(message: str) -> str: ...


class PresetNameDialog(Dialog[str]):
    def __init__(self, master: tk.Misc, initial: str = ""):
        super().__init__(master)
        lang_mgr.register(self, N_("New Preset Name"), "title")

        label_frame = ttk.Frame(self.main_frame)
        label_frame.pack(fill="x")
        label = ttk.Label(label_frame)
        lang_mgr.register(label, N_("Enter name for new preset:"))
        label.pack(anchor="w")

        vcmd = (self.master.register(self.validate), "%P")
        self.entry_var = tk.StringVar(value=initial)
        entry = ttk.Entry(
            self.main_frame,
            validate="key",
            validatecommand=vcmd,
            width=30,
            textvariable=self.entry_var,
        )
        self.set_initial_focus(entry)
        entry.pack()

        option_frame = ttk.Frame(self.main_frame)
        option_frame.pack(fill="x")
        self.allow_non_ascii_var = vars.allow_non_ascii
        allow_non_ascii_cb = ttk.Checkbutton(
            option_frame,
            variable=self.allow_non_ascii_var,
            command=self.non_ascii_warning,
        )
        lang_mgr.register(allow_non_ascii_cb, N_("Allow non-ASCII characters"))
        allow_non_ascii_cb.pack(anchor="w")

        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        ok_button = ttk.Button(button_frame, command=self.on_ok)
        lang_mgr.register(ok_button, N_("OK"))
        ok_button.pack(side=tk.LEFT, padx=10)
        cancel_button = ttk.Button(button_frame, command=self.on_close)
        lang_mgr.register(cancel_button, N_("Cancel"))
        cancel_button.pack(side=tk.LEFT, padx=10)

        self.bind("<Return>", lambda e: self.on_ok())

    def non_ascii_warning(self):
        if self.allow_non_ascii_var.get():
            messagebox.showwarning(
                "Warning",
                _(
                    "The game does not natively support non-ASCII input. "
                    "No bans have been reported so far, "
                    "but proceed with caution and use at your own risk."
                ),
            )
        self.entry_var.set(self.get_correct_input())

    def get_correct_input(self):
        text = self.entry_var.get().strip()
        if not self.allow_non_ascii_var.get():
            text = re.sub(r"[^\x20-\x7E]", "", text)
        return text.encode("utf-16")[:36].decode("utf-16")

    def on_ok(self):
        self.set_result(self.get_correct_input())

    def validate(self, P: str):
        if self.allow_non_ascii_var.get():
            return len(P.encode("utf-16")) < 36
        return re.fullmatch(r"[\x20-\x7E]{0,18}", P) is not None
