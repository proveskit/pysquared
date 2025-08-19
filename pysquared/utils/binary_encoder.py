"""Binary encoding utilities for efficient packet transmission.

This module provides functions to encode and decode int and float values
directly into byte arrays instead of string representations, significantly
reducing packet size and improving transmission efficiency.

**Usage:**
```python
encoder = BinaryEncoder()
encoder.add_float("temperature", 23.5)
encoder.add_int("battery_level", 85)
data = encoder.to_bytes()

decoder = BinaryDecoder(data)
temperature = decoder.get_float("temperature")
battery_level = decoder.get_int("battery_level")
```
"""

import struct
from collections import OrderedDict

try:
    from typing import Dict, Tuple, Union
except ImportError:
    pass


class BinaryEncoder:
    """Encodes data into a compact binary format."""

    def __init__(self) -> None:
        """Initialize the binary encoder."""
        self._data: OrderedDict[str, Tuple[str, Union[int, float, str]]] = OrderedDict()
        self._key_map: Dict[int, str] = {}

    def get_key_map(self) -> Dict[int, str]:
        """Get the key mapping for decoding.

        Returns:
            Dictionary mapping key hashes to key names
        """
        return self._key_map.copy()

    def add_int(self, key: str, value: int, size: int = 4) -> None:
        """Add an integer value.

        Args:
            key: The key name for the value
            value: The integer value
            size: Size in bytes (1, 2, 4, or 8)
        """
        if size == 1:
            fmt = "b" if -128 <= value <= 127 else "B"
        elif size == 2:
            fmt = "h" if -32768 <= value <= 32767 else "H"
        elif size == 4:
            fmt = "i" if -2147483648 <= value <= 2147483647 else "I"
        elif size == 8:
            fmt = "q" if -9223372036854775808 <= value <= 9223372036854775807 else "Q"
        else:
            raise ValueError(f"Unsupported integer size: {size}")

        self._data[key] = (fmt, value)

    def add_float(self, key: str, value: float, double_precision: bool = False) -> None:
        """Add a float value.

        Args:
            key: The key name for the value
            value: The float value
            double_precision: Use double precision (8 bytes) instead of single (4 bytes)
        """
        fmt = "d" if double_precision else "f"
        self._data[key] = (fmt, value)

    def add_string(self, key: str, value: str, max_length: int = 255) -> None:
        """Add a string value with length prefix.

        Args:
            key: The key name for the value
            value: The string value
            max_length: Maximum string length
        """
        encoded_value = value.encode("utf-8")
        if len(encoded_value) > max_length:
            raise ValueError(f"String too long: {len(encoded_value)} > {max_length}")

        # Use 's' format for strings
        self._data[key] = ("s", encoded_value)

    def to_bytes(self) -> bytes:
        """Convert the encoded data to bytes using a compact format.

        Format: [key_hash:4][type:1][data:variable]...

        Returns:
            The binary representation of all added data
        """
        if not self._data:
            return b""

        result = b""

        for key, (fmt, value) in self._data.items():
            # Use a simple hash of the key instead of storing the full key
            key_hash = hash(key) & 0xFFFFFFFF  # 4-byte hash
            self._key_map[key_hash] = key

            if fmt == "s":
                # String: type=0, length + data
                result += struct.pack(">IB", key_hash, 0)  # key_hash + type
                result += struct.pack(">B", len(value)) + value
            elif fmt in "bB":
                # 1-byte int: type=1
                result += struct.pack(
                    ">IBb" if fmt == "b" else ">IBB", key_hash, 1, value
                )
            elif fmt in "hH":
                # 2-byte int: type=2
                result += struct.pack(
                    ">IBh" if fmt == "h" else ">IBH", key_hash, 2, value
                )
            elif fmt in "iI":
                # 4-byte int: type=3
                result += struct.pack(
                    ">IBi" if fmt == "i" else ">IBI", key_hash, 3, value
                )
            elif fmt in "qQ":
                # 8-byte int: type=4
                result += struct.pack(
                    ">IBq" if fmt == "q" else ">IBQ", key_hash, 4, value
                )
            elif fmt == "f":
                # 4-byte float: type=5
                result += struct.pack(">IBf", key_hash, 5, value)
            elif fmt == "d":
                # 8-byte float: type=6
                result += struct.pack(">IBd", key_hash, 6, value)

        return result


class BinaryDecoder:
    """Decodes data from binary format."""

    def __init__(self, data: bytes, key_map: Dict[int, str] = None) -> None:
        """Initialize the binary decoder.

        Args:
            data: The binary data to decode
            key_map: Optional mapping from hash to key name
        """
        self._data: Dict[str, Union[int, float, str]] = {}
        self._key_map = key_map or {}
        self._parse(data)

    def _parse(self, data: bytes) -> None:
        """Parse the binary data."""
        if not data:
            return

        offset = 0

        while offset < len(data):
            if offset + 5 > len(data):  # Need at least 5 bytes (4 + 1)
                break

            # Read key hash and type
            key_hash, data_type = struct.unpack(">IB", data[offset : offset + 5])
            offset += 5

            # Get key name from hash or use hash as string
            key_name = self._key_map.get(key_hash, f"field_{key_hash:08x}")

            if data_type == 0:  # String
                if offset + 1 > len(data):
                    break
                str_len = struct.unpack(">B", data[offset : offset + 1])[0]
                offset += 1

                if offset + str_len > len(data):
                    break
                self._data[key_name] = data[offset : offset + str_len].decode("utf-8")
                offset += str_len

            elif data_type == 1:  # 1-byte int
                if offset + 1 > len(data):
                    break
                self._data[key_name] = struct.unpack(">b", data[offset : offset + 1])[0]
                offset += 1

            elif data_type == 2:  # 2-byte int
                if offset + 2 > len(data):
                    break
                self._data[key_name] = struct.unpack(">h", data[offset : offset + 2])[0]
                offset += 2

            elif data_type == 3:  # 4-byte int
                if offset + 4 > len(data):
                    break
                self._data[key_name] = struct.unpack(">i", data[offset : offset + 4])[0]
                offset += 4

            elif data_type == 4:  # 8-byte int
                if offset + 8 > len(data):
                    break
                self._data[key_name] = struct.unpack(">q", data[offset : offset + 8])[0]
                offset += 8

            elif data_type == 5:  # 4-byte float
                if offset + 4 > len(data):
                    break
                self._data[key_name] = struct.unpack(">f", data[offset : offset + 4])[0]
                offset += 4

            elif data_type == 6:  # 8-byte float
                if offset + 8 > len(data):
                    break
                self._data[key_name] = struct.unpack(">d", data[offset : offset + 8])[0]
                offset += 8
            else:
                # Unknown type, skip
                break

    def get_int(self, key: str) -> int | None:
        """Get an integer value.

        Args:
            key: The key name

        Returns:
            The integer value or None if not found
        """
        value = self._data.get(key)
        return int(value) if value is not None else None

    def get_float(self, key: str) -> float | None:
        """Get a float value.

        Args:
            key: The key name

        Returns:
            The float value or None if not found
        """
        value = self._data.get(key)
        return float(value) if value is not None else None

    def get_string(self, key: str) -> str | None:
        """Get a string value.

        Args:
            key: The key name

        Returns:
            The string value or None if not found
        """
        value = self._data.get(key)
        return str(value) if value is not None else None

    def get_all(self) -> Dict[str, Union[int, float, str]]:
        """Get all decoded data.

        Returns:
            Dictionary containing all decoded key-value pairs
        """
        return self._data.copy()
