import platform
import tkinter as tk

from . import vars
from .int_dialog import IntDialog
from .preset_name_dialog import PresetNameDialog
from .relic_type_dialog import RelicTypeDialog
from .vars import root

if platform.system() == "Darwin":  # macOS
    RIGHT_COMMAND = "<Button-2>"
else:
    RIGHT_COMMAND = "<Button-3>"


def ask_for_relic_type(master: tk.Misc):
    return RelicTypeDialog(master).wait()


def ask_for_preset_name(master: tk.Misc, initial=""):
    return PresetNameDialog(master, initial).wait()


def ask_for_int(
    master: tk.Misc,
    title="",
    prompt="",
    initial: int | None = None,
    note="",
):
    return IntDialog(master, title, prompt, initial, note).wait()
