import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from .dialog import Dialog

# Forward declaration for IDE/Linter support
if TYPE_CHECKING:

    def _(message: str) -> str: ...


class IntDialog(Dialog[int]):
    def __init__(
        self,
        master: tk.Misc,
        title="",
        prompt="",
        initial: int | None = None,
        note="",
    ):
        super().__init__(master, title)

        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill="x", pady=15)
        label = ttk.Label(input_frame, text=prompt)
        label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        vcmd = (self.master.register(self.validate), "%P")
        self.entry_var = tk.StringVar(value=str(initial) if initial is not None else "")
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
        ok_button = ttk.Button(button_frame, command=self.on_ok, text=_("OK"))
        ok_button.pack(side="left", padx=5)
        cancel_button = ttk.Button(
            button_frame, command=self.on_close, text=_("Cancel")
        )
        cancel_button.pack(side="left", padx=5)
        self.bind("<Return>", lambda e: self.on_ok())

        if note:
            separator = ttk.Separator(self.main_frame, orient="horizontal")
            separator.pack(fill="x", pady=(0, 15))

            note_label = ttk.Label(
                self.main_frame,
                wraplength=300,
                justify="left",
                style="Secondary.TLabel",
                text=note,
            )
            note_label.pack(fill="x")

    def on_ok(self):
        result_str = self.entry_var.get()
        if result_str.isdigit():
            self.set_result(int(result_str))
        else:
            self.set_result(None)

    def validate(self, P: str):
        return P == "" or P.isdigit()
