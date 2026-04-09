import tkinter as tk
from tkinter import ttk
from typing import Literal

from .dialog import Dialog

RelicType = Literal["normal", "deep"]


class RelicTypeDialogResult:
    def __init__(self, relic_type: RelicType, count: int):
        self.relic_type = relic_type
        self.count = count


class RelicTypeDialog(Dialog[RelicTypeDialogResult]):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, "Select Relic Type")

        ttk.Label(
            self.main_frame,
            text="Select relic type to create.\nNote: Type cannot be changed later.",
            justify=tk.CENTER,
        ).pack(pady=10)

        quantity_frame = ttk.Frame(self.main_frame)
        quantity_frame.pack(pady=(0, 10))
        ttk.Label(
            quantity_frame,
            text="Quantity:",
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.quantity_var = tk.StringVar(value="1")
        vcmd = (self.register(self.on_validate_input), "%P")
        quantity_entry = ttk.Spinbox(
            quantity_frame,
            textvariable=self.quantity_var,
            width=10,
            from_=1,
            to=999,
            validate="key",
            validatecommand=vcmd,
        )
        self.set_initial_focus(quantity_entry)
        quantity_entry.pack(side=tk.LEFT)

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=5)
        ttk.Button(
            btn_frame,
            text="Normal",
            command=lambda: self.set_result(self.calc_result("normal")),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Deep",
            command=lambda: self.set_result(self.calc_result("deep")),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=lambda: self.set_result(self.calc_result(None)),
        ).pack(side=tk.LEFT, padx=5)

    def on_validate_input(self, P: str):
        if P == "":
            return True
        if P.isdigit():
            count = int(P)
            return 1 <= count <= 999
        return False

    def calc_result(self, relic_type: RelicType | None):
        if relic_type is None:
            return None
        try:
            raw_val = self.quantity_var.get()
            quantity = int(raw_val) if raw_val.isdigit() else 1
            quantity = max(1, min(999, quantity))
        except ValueError:
            quantity = 1
        return RelicTypeDialogResult(relic_type, quantity)
