"""Unit tests for the sensor reading error classes."""

import pytest
from pysquared.sensor_reading.error import (
    SensorReadingError,
    SensorReadingTimeoutError,
    SensorReadingUnknownError,
    SensorReadingValueError,
)


def test_sensor_reading_error_base():
    """Test that SensorReadingError can be raised and caught."""
    with pytest.raises(SensorReadingError):
        raise SensorReadingError("Test error")


def test_sensor_reading_error_inheritance():
    """Test that all specific errors inherit from SensorReadingError."""
    assert issubclass(SensorReadingTimeoutError, SensorReadingError)
    assert issubclass(SensorReadingValueError, SensorReadingError)
    assert issubclass(SensorReadingUnknownError, SensorReadingError)


def test_sensor_reading_timeout_error_default_message():
    """Test SensorReadingTimeoutError with default message."""
    error = SensorReadingTimeoutError()
    assert str(error) == "Sensor reading operation timed out."


def test_sensor_reading_timeout_error_custom_message():
    """Test SensorReadingTimeoutError with custom message."""
    custom_message = "Custom timeout message"
    error = SensorReadingTimeoutError(custom_message)
    assert str(error) == custom_message


def test_sensor_reading_timeout_error_raising():
    """Test that SensorReadingTimeoutError can be raised and caught."""
    with pytest.raises(SensorReadingTimeoutError) as exc_info:
        raise SensorReadingTimeoutError("Timeout occurred")

    assert str(exc_info.value) == "Timeout occurred"


def test_sensor_reading_value_error_default_message():
    """Test SensorReadingValueError with default message."""
    error = SensorReadingValueError()
    assert str(error) == "Sensor reading returned an invalid value."


def test_sensor_reading_value_error_custom_message():
    """Test SensorReadingValueError with custom message."""
    custom_message = "Invalid sensor value detected"
    error = SensorReadingValueError(custom_message)
    assert str(error) == custom_message


def test_sensor_reading_value_error_raising():
    """Test that SensorReadingValueError can be raised and caught."""
    with pytest.raises(SensorReadingValueError) as exc_info:
        raise SensorReadingValueError("Value out of range")

    assert str(exc_info.value) == "Value out of range"


def test_sensor_reading_unknown_error_default_message():
    """Test SensorReadingUnknownError with default message."""
    error = SensorReadingUnknownError()
    assert str(error) == "An unknown error occurred during sensor reading."


def test_sensor_reading_unknown_error_custom_message():
    """Test SensorReadingUnknownError with custom message."""
    custom_message = "Mysterious sensor failure"
    error = SensorReadingUnknownError(custom_message)
    assert str(error) == custom_message


def test_sensor_reading_unknown_error_raising():
    """Test that SensorReadingUnknownError can be raised and caught."""
    with pytest.raises(SensorReadingUnknownError) as exc_info:
        raise SensorReadingUnknownError("Unknown failure mode")

    assert str(exc_info.value) == "Unknown failure mode"


def test_error_hierarchy_catching():
    """Test that specific errors can be caught by the base class."""
    # Test that specific errors can be caught as SensorReadingError
    with pytest.raises(SensorReadingError):
        raise SensorReadingTimeoutError("Timeout")

    with pytest.raises(SensorReadingError):
        raise SensorReadingValueError("Invalid value")

    with pytest.raises(SensorReadingError):
        raise SensorReadingUnknownError("Unknown error")


def test_multiple_error_types():
    """Test handling multiple error types in exception handling."""
    errors_to_test = [
        SensorReadingTimeoutError("Timeout"),
        SensorReadingValueError("Bad value"),
        SensorReadingUnknownError("Unknown"),
    ]

    for error in errors_to_test:
        with pytest.raises(SensorReadingError):
            raise error
