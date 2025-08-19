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
    from typing import Dict, Optional, Tuple, Union
except ImportError:
    pass


class BinaryEncoder:
    """Encodes data into a compact binary format."""

    def __init__(self) -> None:
        """Initialize the binary encoder."""
        self._data: OrderedDict[str, Tuple[str, Union[int, float, str, bytes]]] = (
            OrderedDict()
        )
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

            result += self._encode_field(key_hash, fmt, value)

        return result

    def _encode_field(
        self, key_hash: int, fmt: str, value: Union[int, float, str, bytes]
    ) -> bytes:
        """Encode a single field into bytes.

        Args:
            key_hash: Hash of the field key
            fmt: Format string for the field
            value: Value to encode

        Returns:
            Encoded field bytes
        """
        if fmt == "s":
            # String: type=0, length + data
            result = struct.pack(">IB", key_hash, 0)  # key_hash + type
            byte_value = (
                value if isinstance(value, bytes) else str(value).encode("utf-8")
            )
            result += struct.pack(">B", len(byte_value)) + byte_value
            return result
        elif fmt in "bB":
            # 1-byte int: type=1 (signed), type=11 (unsigned)
            type_id = 1 if fmt == "b" else 11
            return struct.pack(
                ">IBb" if fmt == "b" else ">IBB", key_hash, type_id, value
            )
        elif fmt in "hH":
            # 2-byte int: type=2 (signed), type=12 (unsigned)
            type_id = 2 if fmt == "h" else 12
            return struct.pack(
                ">IBh" if fmt == "h" else ">IBH", key_hash, type_id, value
            )
        elif fmt in "iI":
            # 4-byte int: type=3 (signed), type=13 (unsigned)
            type_id = 3 if fmt == "i" else 13
            return struct.pack(
                ">IBi" if fmt == "i" else ">IBI", key_hash, type_id, value
            )
        elif fmt in "qQ":
            # 8-byte int: type=4 (signed), type=14 (unsigned)
            type_id = 4 if fmt == "q" else 14
            return struct.pack(
                ">IBq" if fmt == "q" else ">IBQ", key_hash, type_id, value
            )
        elif fmt == "f":
            # 4-byte float: type=5
            return struct.pack(">IBf", key_hash, 5, value)
        elif fmt == "d":
            # 8-byte float: type=6
            return struct.pack(">IBd", key_hash, 6, value)
        else:
            raise ValueError(f"Unknown format: {fmt}")


class BinaryDecoder:
    """Decodes data from binary format."""

    def __init__(self, data: bytes, key_map: Optional[Dict[int, str]] = None) -> None:
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

            value, consumed = self._decode_field(data, offset, data_type)
            if value is None:
                break  # Failed to decode or unknown type

            self._data[key_name] = value
            offset += consumed

    def _decode_field(
        self, data: bytes, offset: int, data_type: int
    ) -> Tuple[Union[int, float, str, None], int]:
        """Decode a single field from binary data.

        Args:
            data: Binary data
            offset: Current offset in data
            data_type: Type identifier

        Returns:
            Tuple of (decoded_value, bytes_consumed) or (None, 0) if failed
        """
        if data_type == 0:  # String
            if offset + 1 > len(data):
                return None, 0
            str_len = struct.unpack(">B", data[offset : offset + 1])[0]
            offset += 1

            if offset + str_len > len(data):
                return None, 0
            value = data[offset : offset + str_len].decode("utf-8")
            return value, 1 + str_len

        # Define format mappings for numeric types with separate signed/unsigned
        type_formats = {
            1: (">b", 1),  # 1-byte signed int
            2: (">h", 2),  # 2-byte signed int
            3: (">i", 4),  # 4-byte signed int
            4: (">q", 8),  # 8-byte signed int
            5: (">f", 4),  # 4-byte float
            6: (">d", 8),  # 8-byte float
            11: (">B", 1),  # 1-byte unsigned int
            12: (">H", 2),  # 2-byte unsigned int
            13: (">I", 4),  # 4-byte unsigned int
            14: (">Q", 8),  # 8-byte unsigned int
        }

        if data_type in type_formats:
            fmt, size = type_formats[data_type]
            if offset + size > len(data):
                return None, 0
            value = struct.unpack(fmt, data[offset : offset + size])[0]
            return value, size
        else:
            # Unknown type
            return None, 0

    def get_int(self, key: str) -> Optional[int]:
        """Get an integer value.

        Args:
            key: The key name

        Returns:
            The integer value or None if not found
        """
        value = self._data.get(key)
        return int(value) if value is not None else None

    def get_float(self, key: str) -> Optional[float]:
        """Get a float value.

        Args:
            key: The key name

        Returns:
            The float value or None if not found
        """
        value = self._data.get(key)
        return float(value) if value is not None else None

    def get_string(self, key: str) -> Optional[str]:
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
