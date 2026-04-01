from pathlib import Path


class Packer:
    name: str = "Base"

    @staticmethod
    def check_unpack(save_file: Path) -> bool:
        """Check whether the save file was suitable with this packer."""
        ...

    @staticmethod
    def check_repack(input_dir: Path) -> bool:
        """Check whether the given directory was unpacked by this packer."""
        ...

    @staticmethod
    def unpack(save_file: Path, output_dir: Path) -> None:
        """Unpack all valid entries from the `save_file` to `output_dir`."""
        ...

    @staticmethod
    def repack(input_dir: Path, output_file: Path) -> None:
        """Repack the contents of `input_dir` into `output_file`."""
        ...
