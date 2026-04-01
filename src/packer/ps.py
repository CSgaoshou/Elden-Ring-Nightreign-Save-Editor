import shutil
from pathlib import Path

from ._packer import Packer as _Packer

EXPECTED_SAVE_SIZE = 0x12A00A0
HEADER_SIZE = 0x80
HEADER_MAGIC = b"\x4b\x01\x34\x1b"
USERDATA_CHUNK_SIZE = 0x100000
MAX_USERDATA_CHUNKS = 10
USERDATA_PADDING = 0x00100010.to_bytes(4, "little")

FILE_HEADER = "HEADER"
FILE_REGULATION = "REGULATION"
FILE_USERDATA_PREFIX = "USERDATA_"


class Packer(_Packer):
    name = "PS"

    @staticmethod
    def check_unpack(save_file: Path):
        with save_file.open("rb") as f:
            return f.read(4) == HEADER_MAGIC

    @staticmethod
    def check_repack(input_dir):
        return (input_dir / FILE_REGULATION).exists()

    @staticmethod
    def unpack(save_file: Path, output_dir: Path):
        shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        with save_file.open("rb") as f:
            # 1. Extract Header
            header = f.read(HEADER_SIZE)
            if header:
                (output_dir / FILE_HEADER).write_bytes(header)

            # 2. Extract UserData Chunks
            for i in range(MAX_USERDATA_CHUNKS):
                data = f.read(USERDATA_CHUNK_SIZE)
                if not data:
                    break
                (output_dir / f"{FILE_USERDATA_PREFIX}{i}").write_bytes(
                    USERDATA_PADDING + data
                )

            # 3. Extract Regulation
            regulation = f.read()
            if regulation:
                (output_dir / FILE_REGULATION).write_bytes(regulation)

    @staticmethod
    def repack(input_dir: Path, output_file: Path):
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("wb") as out:
            # 1. Header
            header_data = (input_dir / FILE_HEADER).read_bytes()
            if len(header_data) != HEADER_SIZE:
                raise ValueError(
                    f"Invalid header size: {hex(len(header_data))}. "
                    f"Expected {hex(HEADER_SIZE)} bytes."
                )
            out.write(header_data)

            # 2. Userdata 0–9
            for i in range(MAX_USERDATA_CHUNKS):
                userdata_path = input_dir / f"{FILE_USERDATA_PREFIX}{i}"
                if not userdata_path.is_file():
                    if i != 0:
                        break
                    # USERDATA_0 is required
                    raise FileNotFoundError(f"Required file not found: {userdata_path}")

                block = userdata_path.read_bytes()
                # Validate block has data
                # PS4 USERDATA should start with specified bytes padding
                # If padding exists, strip it. If not, write as-is (kept original logic)
                if len(block) < len(USERDATA_PADDING):
                    raise ValueError(
                        f"{FILE_USERDATA_PREFIX}{i} is too small ({len(block)} bytes)"
                    )
                if block[: len(USERDATA_PADDING)] == USERDATA_PADDING:
                    block = block[len(USERDATA_PADDING) :]
                out.write(block)

            # 3. Regulation
            regulation_path = input_dir / FILE_REGULATION
            if regulation_path.is_file():
                regulation_data = regulation_path.read_bytes()
                if regulation_data:
                    out.write(regulation_data)

        # 4. Size Validation
        final_size = output_file.stat().st_size
        if final_size != EXPECTED_SAVE_SIZE:
            raise ValueError(
                f"Invalid output file size!\n"
                f"Expected: {hex(EXPECTED_SAVE_SIZE)} ({EXPECTED_SAVE_SIZE:,} bytes)\n"
                f"Got: {hex(final_size)} ({final_size:,} bytes)\n"
                f"Difference: {final_size - EXPECTED_SAVE_SIZE:+,} bytes\n\n"
                f"File may be corrupt. Check the source files in {input_dir}"
            )
