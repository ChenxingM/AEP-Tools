"""Low-level binary reader with configurable endianness."""

from __future__ import annotations
import struct
import math


class BitFlags:
    """Bit-level flag accessor for byte arrays."""

    def __init__(self, data: bytes):
        self._data = data

    def get_bit(self, byte_index: int, bit_index: int) -> bool:
        if byte_index >= len(self._data):
            return False
        return (self._data[byte_index] & (1 << bit_index)) != 0


class BinaryReader:
    """Sequential binary data reader with endianness support."""

    def __init__(self, data: bytes | bytearray | memoryview, offset: int = 0,
                 big_endian: bool = True):
        if isinstance(data, memoryview):
            self._data = data
        else:
            self._data = memoryview(bytearray(data))
        self.offset = offset
        self.big_endian = big_endian

    @property
    def _bo(self) -> str:
        return "big" if self.big_endian else "little"

    @property
    def _fmt_prefix(self) -> str:
        return ">" if self.big_endian else "<"

    def read_bytes(self, n: int) -> bytes:
        end = self.offset + n
        if end > len(self._data):
            raise ValueError(
                f"Read past end of data: offset {self.offset}, "
                f"requested {n} bytes, available {len(self._data) - self.offset}"
            )
        result = bytes(self._data[self.offset:end])
        self.offset = end
        return result

    def read_uint(self, n: int) -> int:
        data = self.read_bytes(n)
        return int.from_bytes(data, byteorder=self._bo, signed=False)

    def read_sint(self, n: int) -> int:
        data = self.read_bytes(n)
        return int.from_bytes(data, byteorder=self._bo, signed=True)

    def read_float32(self) -> float:
        data = self.read_bytes(4)
        val = struct.unpack(f"{self._fmt_prefix}f", data)[0]
        return val

    def read_float64(self) -> float:
        data = self.read_bytes(8)
        val = struct.unpack(f"{self._fmt_prefix}d", data)[0]
        return val

    def read_id(self) -> str:
        return self.read_string("ascii", 4)

    def read_string(self, encoding: str, length: int) -> str:
        data = self.read_bytes(length)
        if encoding == "utf-16":
            # Detect BOM or default to big-endian
            if len(data) >= 2:
                if data[0] == 0xFF and data[1] == 0xFE:
                    encoding = "utf-16-le"
                elif data[0] == 0xFE and data[1] == 0xFF:
                    encoding = "utf-16-be"
                else:
                    encoding = "utf-16-le"
        return data.decode(encoding, errors="replace")

    def read_nul_string(self, encoding: str, length: int) -> str:
        data = self.read_bytes(length)
        nul = data.find(0)
        if nul != -1:
            data = data[:nul]
        return data.decode(encoding, errors="replace")

    def read_flags(self, n: int) -> BitFlags:
        return BitFlags(self.read_bytes(n))

    def read_array(self, count: int, read_fn) -> list:
        return [read_fn() for _ in range(count)]

    def skip(self, n: int) -> None:
        if self.offset + n > len(self._data):
            raise ValueError(
                f"Skip past end of data: offset {self.offset}, "
                f"requested {n} bytes, available {len(self._data) - self.offset}"
            )
        self.offset += n

    def remaining(self) -> int:
        return len(self._data) - self.offset

    def sub_reader(self, offset: int, length: int | None = None) -> BinaryReader:
        """Create a new reader sharing the same underlying buffer."""
        if length is None:
            end = len(self._data)
        else:
            end = offset + length
        return BinaryReader(self._data[offset:end], 0, self.big_endian)

    @staticmethod
    def process_speed_value(val: float) -> float:
        return 0.0 if math.isnan(val) else val
