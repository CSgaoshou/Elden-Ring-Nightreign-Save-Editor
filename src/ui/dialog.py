import tkinter as tk
from tkinter import ttk
from typing import Generic, TypeVar, Protocol

_T = TypeVar("_T")


class _Selectable(Protocol):
    def focus(self): ...
    def selection_range(self, start: str | int, end: str | int): ...


class Dialog(tk.Toplevel, Generic[_T]):
    def __init__(self, master: tk.Misc, title=""):
        super().__init__(master)
        self.initial_focus: _Selectable | None = None
        self.title(title)
        self.resizable(False, False)
        self.result: _T | None = None
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Escape>", lambda e: self.on_close())
        self.withdraw()

    def wait(self):
        self.transient(self.master)
        self.grab_set()
        self.focus_set()
        self.display_at_center()
        if self.initial_focus is not None:
            self.initial_focus.focus()
            self.initial_focus.selection_range(0, tk.END)
        self.wait_window()
        return self.result

    def display_at_center(self, parent: tk.Misc | None = None):
        parent = parent or self.master
        self.update_idletasks()
        parent.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        x = parent_x + (parent_w // 2) - (w // 2)
        y = parent_y + (parent_h // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def set_result(self, value: _T | None):
        """Set `self.result` and destroy dialog"""
        self.result = value
        self.destroy()

    def on_close(self):
        self.set_result(None)

    def set_initial_focus(self, widget: _Selectable | None):
        self.initial_focus = widget
