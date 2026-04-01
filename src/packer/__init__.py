from pathlib import Path

from . import pc, ps
from ._packer import Packer

__all__ = ["unpack", "repack", "detect_unpacker", "detect_repacker", "Packer"]

_all_packers: list[type[Packer]] = [
    pc.Packer,
    ps.Packer,
]


def detect_unpacker(save_file: Path | str):
    save_file = Path(save_file)
    for packer in _all_packers:
        if packer.check_unpack(save_file):
            return packer
    raise ValueError(f"Could not find a suitable unpack mode for {save_file.name}")


def detect_repacker(input_dir: Path | str):
    input_dir = Path(input_dir)
    for packer in _all_packers:
        if packer.check_repack(input_dir):
            return packer
    raise ValueError(f"Could not determine the packer from directory {input_dir}")


def unpack(save_file: Path | str, output_dir: Path | str):
    """Unpacks a save file into the specified output directory."""
    save_file = Path(save_file)
    output_dir = Path(output_dir)
    packer = detect_unpacker(save_file)
    packer.unpack(save_file, output_dir)


def repack(input_dir: Path | str, output_file: Path | str):
    """Repacks an unpacked directory back into a save file."""
    input_dir = Path(input_dir)
    output_file = Path(output_file)
    packer = detect_repacker(input_dir)
    packer.repack(input_dir, output_file)
