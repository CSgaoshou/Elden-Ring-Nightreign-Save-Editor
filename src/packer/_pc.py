import hashlib
import logging
import mmap
import shutil
import struct
from dataclasses import dataclass, field

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ._packer import Packer
from ._registry import PackerRegistry

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

    @property
    def decrpyted_size(self) -> int:
        return self.size - IV_SIZE

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


def parse_bnd4(data: bytes) -> list[BND4Entry]:
    if data[:4] != BND4_MAGIC:
        raise ValueError("BND4 magic header not found! Invalid SL2 file.")

    entries: list[BND4Entry] = []
    # Read number of entries (offset 12, 4 bytes, little-endian int)
    num_entries = struct.unpack_from("<i", data, 12)[0]
    logger.info(f"Detected BND4 archive with {num_entries} entries.")

    for i in range(num_entries):
        pos = BND4_HEADER_LEN + (BND4_ENTRY_HEADER_LEN * i)

        # Read Entry Magic
        magic = data[pos : pos + 8]
        if magic != BND4_ENTRY_MAGIC:
            logger.warning(f"Skipping entry {i}: Invalid entry magic.")
            continue

        # Unpack remaining header values
        size, _, data_offset, name_offset, footer_length = struct.unpack_from(
            "<i i i i i", data, pos + 8
        )

        # Sanity checks
        if size <= 0 or data_offset <= 0 or data_offset + size > len(data):
            logger.warning(f"Skipping entry {i}: Invalid size or bounds.")
            continue

        entry = BND4Entry(
            index=i,
            size=size,
            data_offset=data_offset,
            name_offset=name_offset,
            footer_length=footer_length,
            encrypted_data=bytes(data[data_offset : data_offset + size]),
        )
        entries.append(entry)
    return entries


@PackerRegistry.register("PC")
class PCPacker(Packer):
    @classmethod
    def probe_unpack(cls, file_path):
        with file_path.open("rb") as f:
            return f.read(4) == BND4_MAGIC

    @classmethod
    def probe_repack(cls, input_dir):
        return (input_dir / "raw.dat").exists()

    def unpack(self, file_path, output_dir):
        raw_data = file_path.read_bytes()
        entries = parse_bnd4(raw_data)

        shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "raw.dat").write_bytes(raw_data)

        for entry in entries:
            try:
                decrypted = entry.decrypt()
                output_path = output_dir / entry.filename
                output_path.write_bytes(decrypted)
                logger.debug(f"Decrypted: {entry.filename}")
            except Exception as e:
                logger.error(f"Failed to decrypt entry {entry.index}: {e}")

    def repack(self, input_dir, output_file):
        # We start with the original bytes to preserve the exact BND4 structure/headers
        raw_data = (input_dir / "raw.dat").read_bytes()
        entries = parse_bnd4(raw_data)
        new_sl2_data = bytearray(raw_data)

        for entry in entries:
            file_path = input_dir / entry.filename
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Modified file {entry.filename} not found in input directory."
                )

            # 1. Load modified data
            modified_data = file_path.read_bytes()
            if len(modified_data) != entry.decrpyted_size:
                raise ValueError(
                    f"Size of modified file {entry.filename} does not match original size."
                )

            entry.decrypted_data = bytearray(modified_data)

            # 2. Patch checksum
            entry.patch_checksum()

            # 3. Encrypt data back to AES-CBC
            encrypted_data = entry.encrypt()

            # 4. Inject back into the BND4 byte structure
            start = entry.data_offset
            end = start + len(encrypted_data)
            new_sl2_data[start:end] = encrypted_data

        # Write the final SL2 file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(new_sl2_data)

    def read_steam_id(self, unpack_dir):
        userdata_10 = unpack_dir / "USERDATA_10"
        with userdata_10.open("rb") as f:
            return f.read(16)[8:]

    def patch_steam_id(self, userdata_file, steam_id):
        unpack_dir = userdata_file.parent
        original_steam_id = self.read_steam_id(unpack_dir)
        with userdata_file.open("r+b") as f:
            with mmap.mmap(f.fileno(), 0) as mm:
                pos = 0
                while True:
                    pos = mm.find(original_steam_id, pos)
                    if pos == -1:
                        break
                    mm[pos : pos + len(steam_id)] = steam_id
                    pos += len(steam_id)
