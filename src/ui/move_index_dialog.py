import tkinter as tk
from tkinter import ttk

from language_manager import N_, lang_mgr

from .dialog import Dialog


class MoveIndexDialog(Dialog[str]):
    def __init__(self, master: tk.Misc):
        super().__init__(master)
        lang_mgr.register(self, N_("Move Index"), "title")

        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill="x", pady=15)
        label = ttk.Label(input_frame)
        lang_mgr.register(label, N_("Move to After (#):"))
        label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        vcmd = (self.master.register(self.validate), "%P")
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(
            input_frame,
            validate="key",
            validatecommand=vcmd,
            width=15,
            textvariable=self.entry_var,
        )
        self.set_initial_focus(self.entry)
        self.entry.grid(row=0, column=1, sticky="we")
        input_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(self.main_frame, padding="0 0 0 15")
        button_frame.pack()
        ok_button = ttk.Button(button_frame, command=self.on_ok)
        lang_mgr.register(ok_button, N_("OK"))
        ok_button.pack(side="left", padx=5)
        cancel_button = ttk.Button(button_frame, command=self.on_close)
        lang_mgr.register(cancel_button, N_("Cancel"))
        cancel_button.pack(side="left", padx=5)
        self.bind("<Return>", lambda e: self.on_ok())

        separator = ttk.Separator(self.main_frame, orient="horizontal")
        separator.pack(fill="x", pady=(0, 15))

        note = ttk.Label(
            self.main_frame,
            wraplength=300,
            justify="left",
            style="Secondary.TLabel",
        )
        lang_mgr.register(
            note,
            N_("Note: This will also affect the 'Acquisition Time' sorting in-game."),
        )
        note.pack(fill="x")

    def on_ok(self):
        self.set_result(self.entry_var.get())

    def validate(self, P: str):
        return P == "" or P.isdigit()
