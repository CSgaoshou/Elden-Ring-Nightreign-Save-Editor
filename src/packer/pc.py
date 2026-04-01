## ALL THIS SCRIPT IS FROM JTESTA AT GITHUB: https://github.com/jtesta/souls_givifier.
# A MODFIED VERSION OF THE SCRIPT TO HANDE DECRYPT AND ENCRYPT OF THE DS2 SL2 FILES.
# ALL THE CREDIT GOES TO JTESTA and Nordgaren: https://github.com/Nordgaren/ArmoredCore6SaveTransferTool

import hashlib
import json
import logging
import shutil
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ._packer import Packer as _Packer

DS2_KEY = b"\x18\xf6\x32\x66\x05\xbd\x17\x8a\x55\x24\x52\x3a\xc0\xa0\xc6\x09"

BND4_MAGIC = b"BND4"
BND4_ENTRY_MAGIC = b"\x40\x00\x00\x00\xff\xff\xff\xff"

BND4_HEADER_LEN = 64
BND4_ENTRY_HEADER_LEN = 32

IV_SIZE = 16
PADDING_SIZE = 12
START_OF_CHECKSUM_DATA = 4
END_OF_CHECKSUM_DATA = PADDING_SIZE + 16  # 28 bytes

logger = logging.getLogger(__name__)


class SL2FormatError(Exception):
    """Raised when the SL2 file does not match expected BND4 format."""

    pass


@dataclass
class BND4Entry:
    index: int
    size: int
    data_offset: int
    name_offset: int
    footer_length: int

    # Payload
    encrypted_data: bytes = b""
    decrypted_data: bytearray = field(default_factory=bytearray)

    @property
    def filename(self) -> str:
        return f"USERDATA_{self.index}"

    @property
    def iv(self) -> bytes:
        """The first 16 bytes of encrypted data is the Initialization Vector (IV)."""
        return self.encrypted_data[:IV_SIZE]

    @property
    def encrypted_payload(self) -> bytes:
        """The actual encrypted payload follows the IV."""
        return self.encrypted_data[IV_SIZE:]

    def decrypt(self) -> bytearray:
        """Decrypts the AES-CBC payload and stores it in decrypted_data."""
        cipher = Cipher(algorithms.AES(DS2_KEY), modes.CBC(self.iv))
        decryptor = cipher.decryptor()

        raw_decrypted = decryptor.update(self.encrypted_payload) + decryptor.finalize()
        self.decrypted_data = bytearray(raw_decrypted)
        return self.decrypted_data

    def patch_checksum(self) -> None:
        """Calculates MD5 hash of the modified data and patches it into the payload."""
        if not self.decrypted_data:
            raise ValueError(
                f"Cannot patch checksum for empty data in entry {self.index}."
            )

        checksum_end = len(self.decrypted_data) - END_OF_CHECKSUM_DATA
        data_for_hash = self.decrypted_data[START_OF_CHECKSUM_DATA:checksum_end]

        # Calculate MD5
        checksum = hashlib.md5(data_for_hash, usedforsecurity=False).digest()

        # Inject checksum into the specific payload position (16 bytes)
        self.decrypted_data[checksum_end : checksum_end + 16] = checksum

    def encrypt(self) -> bytes:
        """Encrypts the currently loaded decrypted_data back to AES-CBC."""
        if not self.decrypted_data:
            raise ValueError(
                f"No decrypted data available to encrypt for entry {self.index}."
            )

        cipher = Cipher(algorithms.AES(DS2_KEY), modes.CBC(self.iv))
        encryptor = cipher.encryptor()

        encrypted_payload = (
            encryptor.update(bytes(self.decrypted_data)) + encryptor.finalize()
        )
        return self.iv + encrypted_payload


class EntryMeta(TypedDict):
    index: int
    size: int
    data_offset: int
    name_offset: int
    footer_length: int
    iv: str


class Meta(TypedDict):
    header: str
    entries: list[EntryMeta]


class Packer(_Packer):
    name = "PC"

    @staticmethod
    def _parse_bnd4(raw_data: bytes):
        """Parses the BND4 header and extracts entry metadata."""
        if raw_data[:4] != BND4_MAGIC:
            raise SL2FormatError("BND4 magic header not found! Invalid SL2 file.")

        entries: list[BND4Entry] = []
        # Read number of entries (offset 12, 4 bytes, little-endian int)
        num_entries = struct.unpack_from("<i", raw_data, 12)[0]
        logger.info(f"Detected BND4 archive with {num_entries} entries.")

        for i in range(num_entries):
            pos = BND4_HEADER_LEN + (BND4_ENTRY_HEADER_LEN * i)

            # Read Entry Magic
            magic = raw_data[pos : pos + 8]
            if magic != BND4_ENTRY_MAGIC:
                logger.warning(f"Skipping entry {i}: Invalid entry magic.")
                continue

            # Unpack remaining header values
            size, _, data_offset, name_offset, footer_length = struct.unpack_from(
                "<i i i i i", raw_data, pos + 8
            )

            # Sanity checks
            if size <= 0 or data_offset <= 0 or data_offset + size > len(raw_data):
                logger.warning(f"Skipping entry {i}: Invalid size or bounds.")
                continue

            entry = BND4Entry(
                index=i,
                size=size,
                data_offset=data_offset,
                name_offset=name_offset,
                footer_length=footer_length,
                encrypted_data=bytes(raw_data[data_offset : data_offset + size]),
            )
            entries.append(entry)
        return entries

    @staticmethod
    def check_unpack(save_file):
        with save_file.open("rb") as f:
            return f.read(4) == BND4_MAGIC

    @staticmethod
    def check_repack(input_dir):
        return (input_dir / "meta.json").exists()

    @staticmethod
    def unpack(save_file: Path, output_dir: Path):
        raw_data = save_file.read_bytes()
        entries = Packer._parse_bnd4(raw_data)

        shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "header": raw_data[:BND4_HEADER_LEN].hex(),
            "entries": [
                {
                    "index": entry.index,
                    "size": entry.size,
                    "data_offset": entry.data_offset,
                    "name_offset": entry.name_offset,
                    "footer_length": entry.footer_length,
                    "iv": entry.iv.hex(),
                }
                for entry in entries
            ],
        }
        (output_dir / "meta.json").write_text(json.dumps(meta, indent=2))

        for entry in entries:
            decrypted = entry.decrypt()
            output_path = output_dir / entry.filename
            output_path.write_bytes(decrypted)

    @staticmethod
    def repack(input_dir: Path, output_file: Path) -> None:
        meta: Meta = json.loads((input_dir / "meta.json").read_text())
        header = bytes.fromhex(meta["header"])
        entries_meta = meta["entries"]

        new_data = bytearray(header)
        entry_table_size = BND4_ENTRY_HEADER_LEN * len(entries_meta)
        new_data.extend(b"\x00" * entry_table_size)
        current_offset = BND4_HEADER_LEN + entry_table_size

        for i, entry_meta in enumerate(entries_meta):
            data = (input_dir / f"USERDATA_{i}").read_bytes()
            entry = BND4Entry(
                index=i,
                size=len(data),
                data_offset=current_offset,
                name_offset=entry_meta["name_offset"],
                footer_length=entry_meta["footer_length"],
                encrypted_data=bytes.fromhex(entry_meta["iv"]),
                decrypted_data=bytearray(data),
            )

            if len(entry.decrypted_data) != entry.size:
                raise ValueError(
                    f"Size mismatch for entry {i}: expected {entry.size} bytes, "
                    f"got {len(entry.decrypted_data)} bytes."
                )

            entry.patch_checksum()
            encrypted = entry.encrypt()
            new_data.extend(encrypted)
            entry_pos = BND4_HEADER_LEN + i * BND4_ENTRY_HEADER_LEN
            struct.pack_into(
                "<8siiiii",
                new_data,
                entry_pos,
                BND4_ENTRY_MAGIC,
                len(encrypted),
                0,
                current_offset,
                entry_meta["name_offset"],
                entry_meta["footer_length"],
            )
            current_offset += len(encrypted)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(new_data)
