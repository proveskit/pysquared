#!/usr/bin/env python3
"""
Demonstration of binary encoding efficiency for satellite beacon data.

This script shows the memory savings achieved by using binary encoding
instead of JSON for satellite telemetry data transmission.
"""

import json
import sys
import time
from pathlib import Path

# Add pysquared to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pysquared.binary_encoder import BinaryDecoder, BinaryEncoder


def create_sample_beacon_data():
    """Create sample beacon data similar to what a satellite would send."""
    return {
        "name": "PySquared-1",
        "time": "2024-08-19 14:30:45",
        "uptime": 7256.3,  # seconds
        "Processor_0_temperature": 42.8,
        "battery_level": 87,
        "solar_panel_voltage": 4.12,
        "radio_rssi": -85,
        "IMU_0_acceleration_x": 0.023,
        "IMU_0_acceleration_y": -0.157,
        "IMU_0_acceleration_z": 9.798,
        "IMU_0_gyroscope_x": 0.001,
        "IMU_0_gyroscope_y": 0.003,
        "IMU_0_gyroscope_z": -0.002,
        "PowerMonitor_0_current_avg": 0.142,
        "PowerMonitor_0_bus_voltage_avg": 3.31,
        "PowerMonitor_0_shunt_voltage_avg": 0.008,
        "TemperatureSensor_0_temperature": 18.6,
        "TemperatureSensor_0_timestamp": int(time.time()),
        "TemperatureSensor_1_temperature": 22.3,
        "TemperatureSensor_1_timestamp": int(time.time()),
        "Magnetometer_0_x": 25.4,
        "Magnetometer_0_y": -12.8,
        "Magnetometer_0_z": 48.2,
        "LightSensor_0_lux": 1456.7,
        "mission_state": "nominal",
        "error_count": 0,
        "last_command_timestamp": int(time.time()) - 3600,
    }


def encode_with_json(data):
    """Encode data using JSON."""
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


def encode_with_binary(data):
    """Encode data using binary encoding."""
    encoder = BinaryEncoder()

    for key, value in data.items():
        if isinstance(value, str):
            encoder.add_string(key, value)
        elif isinstance(value, float):
            encoder.add_float(key, value)
        elif isinstance(value, int):
            # Optimize int size based on value range
            if -128 <= value <= 127:
                encoder.add_int(key, value, size=1)
            elif -32768 <= value <= 32767:
                encoder.add_int(key, value, size=2)
            else:
                encoder.add_int(key, value, size=4)

    return encoder.to_bytes(), encoder.get_key_map()


def verify_binary_decoding(binary_data, key_map, original_data):
    """Verify that binary decoding produces the original data."""
    decoder = BinaryDecoder(binary_data, key_map)
    decoded_data = decoder.get_all()

    # Check that all keys are present and values match
    for key, original_value in original_data.items():
        decoded_value = decoded_data.get(key)
        if isinstance(original_value, float):
            # Allow small floating point differences
            assert decoded_value is not None, f"Missing decoded value for {key}"
            assert isinstance(decoded_value, (int, float)), (
                f"Expected numeric value for {key}, got {type(decoded_value)}"
            )
            assert abs(float(decoded_value) - original_value) < 0.001, (
                f"Float mismatch for {key}: {decoded_value} != {original_value}"
            )
        else:
            assert decoded_value == original_value, (
                f"Value mismatch for {key}: {decoded_value} != {original_value}"
            )

    print("✓ Binary encoding/decoding verification passed!")
    return decoded_data


def analyze_packet_overhead():
    """Analyze overhead when data is sent through the packet system."""
    print("\n=== PACKET SYSTEM ANALYSIS ===")

    # Simulate packet manager overhead (6 bytes header)
    packet_header_size = 6

    sample_data = create_sample_beacon_data()

    # JSON approach
    json_payload = encode_with_json(sample_data)
    json_total_with_header = len(json_payload) + packet_header_size

    # Binary approach
    binary_payload, key_map = encode_with_binary(sample_data)
    binary_total_with_header = len(binary_payload) + packet_header_size

    # Calculate savings including packet overhead
    total_savings = json_total_with_header - binary_total_with_header
    total_savings_percent = (total_savings / json_total_with_header) * 100

    print(f"JSON payload: {len(json_payload)} bytes")
    print(f"Binary payload: {len(binary_payload)} bytes")
    print(f"Packet header: {packet_header_size} bytes")
    print(f"Total JSON packet: {json_total_with_header} bytes")
    print(f"Total binary packet: {binary_total_with_header} bytes")
    print(f"Total savings: {total_savings} bytes ({total_savings_percent:.1f}%)")

    return {
        "json_payload_size": len(json_payload),
        "binary_payload_size": len(binary_payload),
        "total_json_size": json_total_with_header,
        "total_binary_size": binary_total_with_header,
        "savings_bytes": total_savings,
        "savings_percent": total_savings_percent,
    }


def main():
    """Run the binary encoding demonstration."""
    print("=== BINARY ENCODING EFFICIENCY DEMONSTRATION ===")
    print("Comparing JSON vs Binary encoding for satellite beacon data\n")

    # Create sample data
    sample_data = create_sample_beacon_data()
    print(f"Sample beacon data contains {len(sample_data)} fields")

    # Encode with JSON
    json_data = encode_with_json(sample_data)
    print(f"JSON encoding: {len(json_data)} bytes")

    # Encode with binary
    binary_data, key_map = encode_with_binary(sample_data)
    print(f"Binary encoding: {len(binary_data)} bytes")

    # Calculate savings
    savings = len(json_data) - len(binary_data)
    savings_percent = (savings / len(json_data)) * 100

    print("\n=== EFFICIENCY RESULTS ===")
    print(f"JSON size: {len(json_data)} bytes")
    print(f"Binary size: {len(binary_data)} bytes")
    print(f"Space savings: {savings} bytes ({savings_percent:.1f}%)")
    print(f"Compression ratio: {len(json_data) / len(binary_data):.2f}x")

    # Verify decoding works correctly
    print("\n=== VERIFICATION ===")
    decoded_data = verify_binary_decoding(binary_data, key_map, sample_data)
    print(f"Successfully decoded {len(decoded_data)} fields")

    # Analyze with packet system overhead
    packet_analysis = analyze_packet_overhead()

    # Show transmission benefits
    print("\n=== TRANSMISSION BENEFITS ===")
    print("For a typical satellite beacon interval (every 30 seconds):")
    daily_transmissions = 24 * 60 * 2  # 2 transmissions per minute
    daily_json_bytes = daily_transmissions * packet_analysis["total_json_size"]
    daily_binary_bytes = daily_transmissions * packet_analysis["total_binary_size"]
    daily_savings = daily_json_bytes - daily_binary_bytes

    print(f"Daily transmissions: {daily_transmissions}")
    print(
        f"Daily JSON data: {daily_json_bytes:,} bytes ({daily_json_bytes / 1024:.1f} KB)"
    )
    print(
        f"Daily binary data: {daily_binary_bytes:,} bytes ({daily_binary_bytes / 1024:.1f} KB)"
    )
    print(
        f"Daily bandwidth savings: {daily_savings:,} bytes ({daily_savings / 1024:.1f} KB)"
    )

    print("\n=== SUMMARY ===")
    print(f"✓ Binary encoding reduces packet size by {savings_percent:.1f}%")
    print(f"✓ Each beacon transmission saves {packet_analysis['savings_bytes']} bytes")
    print(f"✓ Daily bandwidth savings: {daily_savings / 1024:.1f} KB")
    print("✓ Encoding/decoding works correctly for all data types")
    print("✓ System supports int, float, and string data efficiently")


if __name__ == "__main__":
    main()
