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

    def add_int(self, key: str, value: int, size: int | None = None) -> None:
        """Add an integer value.

        Args:
            key: The key name for the value
            value: The integer value
            size: Size in bytes (1, 2, 4, or 8). If None, automatically determined based on value range.
        """
        if size is None:
            size = self._determine_int_size(value)

        fmt = self._get_int_format(size, value)
        self._data[key] = (fmt, value)

    def _determine_int_size(self, value: int) -> int:
        """Determine the optimal size for an integer value.

        Args:
            value: The integer value

        Returns:
            Size in bytes (1, 2, 4, or 8)
        """
        if -128 <= value <= 255:  # Fits in 1 byte
            return 1
        elif -32768 <= value <= 32767:  # Fits in 2 bytes
            return 2
        elif -2147483648 <= value <= 2147483647:  # Fits in 4 bytes
            return 4
        else:  # Use 8 bytes for large values
            return 8

    def _get_int_format(self, size: int, value: int) -> str:
        """Get the struct format string for an integer.

        Args:
            size: Size in bytes
            value: The integer value

        Returns:
            Struct format string

        Raises:
            ValueError: If size is not supported
        """
        size_ranges = {
            1: (-128, 127, "b", "B"),
            2: (-32768, 32767, "h", "H"),
            4: (-2147483648, 2147483647, "i", "I"),
            8: (-9223372036854775808, 9223372036854775807, "q", "Q"),
        }

        if size not in size_ranges:
            raise ValueError(f"Unsupported integer size: {size}")

        min_val, max_val, signed_fmt, unsigned_fmt = size_ranges[size]
        return signed_fmt if min_val <= value <= max_val else unsigned_fmt

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

    # Format type constants for better readability
    _STRING_FORMATS = {"s"}
    _INTEGER_FORMATS = {"b", "B", "h", "H", "i", "I", "q", "Q"}
    _FLOAT_FORMATS = {"f", "d"}

    def _encode_field(
        self, key_hash: int, fmt: str, value: Union[int, float, str, bytes]
    ) -> bytes:
        """Encode a single field into bytes.

        Dispatches to the appropriate encoding method based on format type.

        Args:
            key_hash: Hash of the field key
            fmt: Format string for the field
            value: Value to encode

        Returns:
            Encoded field bytes
        """
        if self._is_string_format(fmt):
            return self._encode_string_field(key_hash, value)
        elif self._is_integer_format(fmt):
            return self._encode_integer_field(key_hash, fmt, value)
        elif self._is_float_format(fmt):
            return self._encode_float_field(key_hash, fmt, value)
        else:
            raise ValueError(f"Unknown format: {fmt}")

    def _is_string_format(self, fmt: str) -> bool:
        """Check if format represents a string type."""
        return fmt in self._STRING_FORMATS

    def _is_integer_format(self, fmt: str) -> bool:
        """Check if format represents an integer type."""
        return fmt in self._INTEGER_FORMATS

    def _is_float_format(self, fmt: str) -> bool:
        """Check if format represents a float type."""
        return fmt in self._FLOAT_FORMATS

    def _encode_string_field(
        self, key_hash: int, value: Union[int, float, str, bytes]
    ) -> bytes:
        """Encode a string field into bytes.

        Args:
            key_hash: Hash of the field key
            value: Value to encode as string

        Returns:
            Encoded string field bytes
        """
        result = struct.pack(">IB", key_hash, 0)
        byte_value = value if isinstance(value, bytes) else str(value).encode("utf-8")
        result += struct.pack(">B", len(byte_value)) + byte_value
        return result

    def _encode_integer_field(
        self, key_hash: int, fmt: str, value: Union[int, float, str, bytes]
    ) -> bytes:
        """Encode an integer field into bytes.

        Args:
            key_hash: Hash of the field key
            fmt: Format string for the integer
            value: Value to encode as integer

        Returns:
            Encoded integer field bytes
        """
        type_info = self._get_integer_type_info(fmt)
        return struct.pack(
            type_info["struct_format"], key_hash, type_info["type_id"], int(value)
        )

    def _encode_float_field(
        self, key_hash: int, fmt: str, value: Union[int, float, str, bytes]
    ) -> bytes:
        """Encode a float field into bytes.

        Args:
            key_hash: Hash of the field key
            fmt: Format string for the float
            value: Value to encode as float

        Returns:
            Encoded float field bytes
        """
        type_id = 5 if fmt == "f" else 6
        struct_format = f">IB{fmt}"
        return struct.pack(struct_format, key_hash, type_id, float(value))

    def _get_integer_type_info(self, fmt: str) -> dict:
        """Get type information for integer formats.

        Args:
            fmt: Format string for the integer

        Returns:
            Dictionary containing type_id and struct_format
        """
        integer_types = {
            "b": {"type_id": 1, "struct_format": ">IBb"},
            "B": {"type_id": 11, "struct_format": ">IBB"},
            "h": {"type_id": 2, "struct_format": ">IBh"},
            "H": {"type_id": 12, "struct_format": ">IBH"},
            "i": {"type_id": 3, "struct_format": ">IBi"},
            "I": {"type_id": 13, "struct_format": ">IBI"},
            "q": {"type_id": 4, "struct_format": ">IBq"},
            "Q": {"type_id": 14, "struct_format": ">IBQ"},
        }
        return integer_types[fmt]


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
