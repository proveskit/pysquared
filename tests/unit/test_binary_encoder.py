"""Tests for the binary encoder module."""

from unittest.mock import patch

import pytest

from pysquared.binary_encoder import BinaryDecoder, BinaryEncoder


class TestBinaryEncoder:
    """Test cases for BinaryEncoder."""

    def test_empty_encoder(self):
        """Test encoding with no data."""
        encoder = BinaryEncoder()
        data = encoder.to_bytes()
        assert data == b""  # Empty data

    def test_single_int(self):
        """Test encoding a single integer."""
        encoder = BinaryEncoder()
        encoder.add_int("test_int", 42)
        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_int("test_int") == 42

    def test_single_float(self):
        """Test encoding a single float."""
        encoder = BinaryEncoder()
        encoder.add_float("test_float", 3.14159)
        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        result = decoder.get_float("test_float")
        assert result is not None
        assert abs(result - 3.14159) < 0.0001  # Account for float precision

    def test_single_string(self):
        """Test encoding a single string."""
        encoder = BinaryEncoder()
        encoder.add_string("test_string", "Hello World")
        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_string("test_string") == "Hello World"

    def test_mixed_data_types(self):
        """Test encoding multiple data types."""
        encoder = BinaryEncoder()
        encoder.add_int("count", 100)
        encoder.add_float("temperature", 23.5)
        encoder.add_string("name", "MySat")
        encoder.add_int("battery", 85, size=1)  # Small int

        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_int("count") == 100
        temp_result = decoder.get_float("temperature")
        assert temp_result is not None
        assert abs(temp_result - 23.5) < 0.01
        assert decoder.get_string("name") == "MySat"
        assert decoder.get_int("battery") == 85

    def test_int_sizes(self):
        """Test different integer sizes."""
        encoder = BinaryEncoder()
        encoder.add_int("small", 127, size=1)
        encoder.add_int("medium", 32767, size=2)
        encoder.add_int("large", 2147483647, size=4)

        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_int("small") == 127
        assert decoder.get_int("medium") == 32767
        assert decoder.get_int("large") == 2147483647

    def test_negative_numbers(self):
        """Test encoding negative numbers."""
        encoder = BinaryEncoder()
        encoder.add_int("neg_int", -42)
        encoder.add_float("neg_float", -3.14)

        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_int("neg_int") == -42
        neg_float_result = decoder.get_float("neg_float")
        assert neg_float_result is not None
        assert abs(neg_float_result - (-3.14)) < 0.01

    def test_double_precision_float(self):
        """Test double precision float encoding."""
        encoder = BinaryEncoder()
        encoder.add_float("double_val", 3.141592653589793, double_precision=True)

        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        result = decoder.get_float("double_val")
        assert result is not None
        assert abs(result - 3.141592653589793) < 0.000000000001

    def test_empty_string(self):
        """Test encoding empty string."""
        encoder = BinaryEncoder()
        encoder.add_string("empty", "")

        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_string("empty") == ""

    def test_unicode_string(self):
        """Test encoding unicode string."""
        encoder = BinaryEncoder()
        encoder.add_string("unicode", "Temperature: 25°C")

        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_string("unicode") == "Temperature: 25°C"

    def test_long_key_no_error(self):
        """Test that long keys work with hash-based approach."""
        encoder = BinaryEncoder()
        long_key = "x" * 256  # Long key is fine with hash-based approach

        encoder.add_string(long_key, "value")
        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_string(long_key) == "value"

    def test_string_too_long_error(self):
        """Test error with string that's too long."""
        encoder = BinaryEncoder()
        long_string = "x" * 256  # Too long for default max_length

        with pytest.raises(ValueError, match="String too long"):
            encoder.add_string("key", long_string)

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        encoder = BinaryEncoder()
        encoder.add_int("existing", 42)
        data = encoder.to_bytes()

        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_int("nonexistent") is None
        assert decoder.get_float("nonexistent") is None
        assert decoder.get_string("nonexistent") is None

    def test_get_all_data(self):
        """Test getting all decoded data."""
        encoder = BinaryEncoder()
        encoder.add_int("count", 100)
        encoder.add_float("temp", 23.5)
        encoder.add_string("name", "Test")

        data = encoder.to_bytes()
        decoder = BinaryDecoder(data, encoder.get_key_map())

        all_data = decoder.get_all()
        assert all_data["count"] == 100
        temp_value = all_data["temp"]
        assert isinstance(temp_value, float)
        assert abs(temp_value - 23.5) < 0.01
        assert all_data["name"] == "Test"

    def test_malformed_data(self):
        """Test decoder with malformed data."""
        # Test with incomplete data
        decoder = BinaryDecoder(b"\x00")  # Just 1 byte
        assert decoder.get_all() == {}

        # Test with empty data
        decoder = BinaryDecoder(b"")
        assert decoder.get_all() == {}

    def test_unsigned_integers(self):
        """Test unsigned integer encoding for large values."""
        encoder = BinaryEncoder()
        # Test unsigned byte (255 will be encoded as 'B' format)
        encoder.add_int("ubyte", 255, size=1)
        # Test unsigned short (65535 will be encoded as 'H' format)
        encoder.add_int("ushort", 65535, size=2)
        # Test unsigned int (4294967295 will be encoded as 'I' format)
        encoder.add_int("uint", 4294967295, size=4)
        # Test unsigned long (18446744073709551615 will be encoded as 'Q' format)
        encoder.add_int("ulong", 18446744073709551615, size=8)

        data = encoder.to_bytes()
        decoder = BinaryDecoder(data, encoder.get_key_map())

        assert decoder.get_int("ubyte") == 255
        assert decoder.get_int("ushort") == 65535
        assert decoder.get_int("uint") == 4294967295
        assert decoder.get_int("ulong") == 18446744073709551615

    def test_invalid_integer_size(self):
        """Test error handling for invalid integer sizes."""
        encoder = BinaryEncoder()
        with pytest.raises(ValueError, match="Unsupported integer size: 3"):
            encoder.add_int("invalid", 42, size=3)

    def test_decoder_edge_cases(self):
        """Test decoder with various edge cases."""
        encoder = BinaryEncoder()
        encoder.add_string("test", "hello")
        data = encoder.to_bytes()

        # Test truncated data scenarios
        # Test with incomplete header
        decoder1 = BinaryDecoder(data[:4], encoder.get_key_map())  # Only 4 bytes
        assert decoder1.get_all() == {}

        # Test with partial string length
        decoder2 = BinaryDecoder(data[:6], encoder.get_key_map())  # Missing string data
        assert decoder2.get_all() == {}

    def test_unknown_data_type(self):
        """Test decoder handling of unknown data types."""
        # Create malformed data with unknown type (type 99)
        malformed_data = b"\x12\x34\x56\x78\x63"  # key_hash + unknown type 99
        decoder = BinaryDecoder(malformed_data)
        assert decoder.get_all() == {}

    def test_decoder_without_key_map(self):
        """Test decoder functionality without key mapping."""
        encoder = BinaryEncoder()
        encoder.add_int("test_key", 42)
        data = encoder.to_bytes()

        # Decode without key map - should use generic field names
        decoder = BinaryDecoder(data)
        decoded = decoder.get_all()

        # Should have one field with a generic name like "field_12345678"
        assert len(decoded) == 1
        assert 42 in decoded.values()

        # Field name should match pattern "field_XXXXXXXX"
        field_name = list(decoded.keys())[0]
        assert field_name.startswith("field_")
        assert len(field_name) == 14  # "field_" + 8 hex chars

    def test_large_string_handling(self):
        """Test handling of strings at the size limit."""
        encoder = BinaryEncoder()
        # Test string at max length (255 bytes)
        max_string = "x" * 255
        encoder.add_string("max_str", max_string)

        data = encoder.to_bytes()
        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_string("max_str") == max_string

    def test_special_float_values(self):
        """Test encoding of special float values."""
        encoder = BinaryEncoder()
        encoder.add_float("zero", 0.0)
        encoder.add_float("negative_zero", -0.0)
        encoder.add_float("small", 1e-10)
        encoder.add_float("large", 1e10)

        data = encoder.to_bytes()
        decoder = BinaryDecoder(data, encoder.get_key_map())

        assert decoder.get_float("zero") == 0.0
        assert decoder.get_float("negative_zero") == -0.0
        small_result = decoder.get_float("small")
        assert small_result is not None
        assert abs(small_result - 1e-10) < 1e-15
        large_result = decoder.get_float("large")
        assert large_result is not None
        assert abs(large_result - 1e10) < 1e5

    def test_unknown_format_error(self):
        """Test error handling for unknown format in _encode_field."""
        encoder = BinaryEncoder()
        # This should not happen in normal usage, but test the error path
        with pytest.raises(ValueError, match="Unknown format"):
            encoder._encode_field(123, "X", 42)

    def test_import_fallback(self):
        """Test that the module works even when typing imports fail."""
        import sys

        # Mock the typing import to fail
        with patch.dict(sys.modules, {"typing": None}):  # type: ignore[attr-defined]
            # Force reimport to test the fallback
            if "pysquared.binary_encoder" in sys.modules:
                del sys.modules["pysquared.binary_encoder"]

            # This should work even without typing imports
            import pysquared.binary_encoder

            # Test that basic functionality still works
            encoder = pysquared.binary_encoder.BinaryEncoder()
            encoder.add_int("test", 42)
            encoder.add_float("temp", 23.5)
            encoder.add_string("name", "test")

            data = encoder.to_bytes()
            decoder = pysquared.binary_encoder.BinaryDecoder(
                data, encoder.get_key_map()
            )

            assert decoder.get_int("test") == 42
            temp_value = decoder.get_float("temp")
            assert temp_value is not None
            assert abs(temp_value - 23.5) < 0.01
            assert decoder.get_string("name") == "test"


class TestBeaconIntegration:
    """Test the binary encoder with realistic beacon data."""

    def test_realistic_beacon_data(self):
        """Test encoding typical beacon sensor data."""
        encoder = BinaryEncoder()

        # Typical beacon data
        encoder.add_string("name", "TestSat")
        encoder.add_string("time", "2024-01-15 10:30:45")
        encoder.add_float("uptime", 3600.5)  # 1 hour uptime
        encoder.add_float("Processor_0_temperature", 45.2)
        encoder.add_int("battery_level", 85, size=1)
        encoder.add_float("IMU_0_acceleration_0", 0.12)
        encoder.add_float("IMU_0_acceleration_1", -0.05)
        encoder.add_float("IMU_0_acceleration_2", 9.81)
        encoder.add_float("PowerMonitor_0_current_avg", 0.125)
        encoder.add_float("PowerMonitor_0_bus_voltage_avg", 3.3)
        encoder.add_float("TemperatureSensor_0_temperature", 22.5)
        encoder.add_int("TemperatureSensor_0_temperature_timestamp", 1705315845)

        data = encoder.to_bytes()

        # Verify data can be decoded correctly
        decoder = BinaryDecoder(data, encoder.get_key_map())
        assert decoder.get_string("name") == "TestSat"
        uptime_result = decoder.get_float("uptime")
        assert uptime_result is not None
        assert abs(uptime_result - 3600.5) < 0.01
        assert decoder.get_int("battery_level") == 85
        accel_result = decoder.get_float("IMU_0_acceleration_2")
        assert accel_result is not None
        assert abs(accel_result - 9.81) < 0.01
        current_result = decoder.get_float("PowerMonitor_0_current_avg")
        assert current_result is not None
        assert abs(current_result - 0.125) < 0.001

        # Don't return data, let test complete normally
        assert len(data) > 0

    def test_memory_efficiency_comparison(self):
        """Test and compare memory efficiency vs JSON."""
        import json
        from collections import OrderedDict

        # Create test data similar to beacon
        state = OrderedDict()
        state["name"] = "TestSat"
        state["time"] = "2024-01-15 10:30:45"
        state["uptime"] = 3600.5
        state["Processor_0_temperature"] = 45.2
        state["battery_level"] = 85
        state["IMU_0_acceleration"] = [0.12, -0.05, 9.81]
        state["IMU_0_gyroscope"] = [0.001, 0.002, -0.001]
        state["PowerMonitor_0_current_avg"] = 0.125
        state["PowerMonitor_0_bus_voltage_avg"] = 3.3
        state["PowerMonitor_0_shunt_voltage_avg"] = 0.01
        state["TemperatureSensor_0_temperature"] = 22.5
        state["TemperatureSensor_0_temperature_timestamp"] = 1705315845

        # JSON encoding
        json_data = json.dumps(state, separators=(",", ":")).encode("utf-8")

        # Binary encoding
        encoder = BinaryEncoder()
        encoder.add_string("name", "TestSat")
        encoder.add_string("time", "2024-01-15 10:30:45")
        encoder.add_float("uptime", 3600.5)
        encoder.add_float("Processor_0_temperature", 45.2)
        encoder.add_int("battery_level", 85, size=1)
        # Handle IMU arrays
        for i, val in enumerate([0.12, -0.05, 9.81]):
            encoder.add_float(f"IMU_0_acceleration_{i}", val)
        for i, val in enumerate([0.001, 0.002, -0.001]):
            encoder.add_float(f"IMU_0_gyroscope_{i}", val)
        encoder.add_float("PowerMonitor_0_current_avg", 0.125)
        encoder.add_float("PowerMonitor_0_bus_voltage_avg", 3.3)
        encoder.add_float("PowerMonitor_0_shunt_voltage_avg", 0.01)
        encoder.add_float("TemperatureSensor_0_temperature", 22.5)
        encoder.add_int("TemperatureSensor_0_temperature_timestamp", 1705315845)

        binary_data = encoder.to_bytes()

        json_size = len(json_data)
        binary_size = len(binary_data)
        savings_percent = ((json_size - binary_size) / json_size) * 100

        # Log results
        print(f"JSON size: {json_size} bytes")
        print(f"Binary size: {binary_size} bytes")
        print(f"Memory savings: {savings_percent:.1f}%")

        # Assert the results - binary should be more efficient
        assert binary_size < json_size, (
            f"Binary ({binary_size}) should be smaller than JSON ({json_size})"
        )
        assert savings_percent > 0, (
            f"Should have positive savings, got {savings_percent:.1f}%"
        )
