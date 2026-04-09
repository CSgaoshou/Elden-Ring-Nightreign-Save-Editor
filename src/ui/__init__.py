import tkinter as tk

from . import vars
from .move_index_dialog import MoveIndexDialog
from .preset_name_dialog import PresetNameDialog
from .relic_type_dialog import RelicTypeDialog
from .vars import root


def ask_for_relic_type(master: tk.Misc):
    return RelicTypeDialog(master).wait()


def ask_for_preset_name(master: tk.Misc, initial=""):
    return PresetNameDialog(master, initial).wait()


def ask_for_move_index(master: tk.Misc):
    return MoveIndexDialog(master).wait()
