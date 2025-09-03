"""Unit tests for the avg_readings helper function."""

from unittest.mock import Mock

import pytest
from pysquared.sensor_reading.avg import avg_readings
from pysquared.sensor_reading.current import Current
from pysquared.sensor_reading.voltage import Voltage


def test_avg_readings_with_current():
    """Test avg_readings with Current sensor readings."""
    # Create mock function that returns Current readings
    mock_func = Mock()
    mock_func.side_effect = [
        Current(10.0),
        Current(20.0),
        Current(30.0),
        Current(40.0),
        Current(50.0),
    ]

    result = avg_readings(mock_func, num_readings=5)

    assert result == 30.0  # Average of 10, 20, 30, 40, 50
    assert mock_func.call_count == 5


def test_avg_readings_with_voltage():
    """Test avg_readings with Voltage sensor readings."""
    # Create mock function that returns Voltage readings
    mock_func = Mock()
    mock_func.side_effect = [
        Voltage(3.0),
        Voltage(3.3),
        Voltage(3.6),
        Voltage(3.9),
        Voltage(4.2),
    ]

    result = avg_readings(mock_func, num_readings=5)

    assert result == 3.6  # Average of 3.0, 3.3, 3.6, 3.9, 4.2
    assert mock_func.call_count == 5


def test_avg_readings_default_num_readings():
    """Test avg_readings with default number of readings (50)."""
    mock_func = Mock()
    mock_func.return_value = Current(5.0)

    result = avg_readings(mock_func)

    assert result == 5.0
    assert mock_func.call_count == 50


def test_avg_readings_single_reading():
    """Test avg_readings with a single reading."""
    mock_func = Mock()
    mock_func.return_value = Voltage(12.5)

    result = avg_readings(mock_func, num_readings=1)

    assert result == 12.5
    assert mock_func.call_count == 1


def test_avg_readings_zero_values():
    """Test avg_readings with zero values."""
    mock_func = Mock()
    mock_func.return_value = Current(0.0)

    result = avg_readings(mock_func, num_readings=10)

    assert result == 0.0
    assert mock_func.call_count == 10


def test_avg_readings_negative_values():
    """Test avg_readings with negative values."""
    mock_func = Mock()
    mock_func.side_effect = [
        Current(-5.0),
        Current(-10.0),
        Current(-15.0),
    ]

    result = avg_readings(mock_func, num_readings=3)

    assert result == -10.0  # Average of -5, -10, -15
    assert mock_func.call_count == 3


def test_avg_readings_mixed_values():
    """Test avg_readings with mixed positive and negative values."""
    mock_func = Mock()
    mock_func.side_effect = [
        Voltage(-5.0),
        Voltage(0.0),
        Voltage(5.0),
        Voltage(10.0),
    ]

    result = avg_readings(mock_func, num_readings=4)

    assert result == 2.5  # Average of -5, 0, 5, 10
    assert mock_func.call_count == 4


def test_avg_readings_precision():
    """Test avg_readings with high precision values."""
    mock_func = Mock()
    mock_func.side_effect = [
        Current(1.111111),
        Current(2.222222),
        Current(3.333333),
    ]

    result = avg_readings(mock_func, num_readings=3)

    expected = (1.111111 + 2.222222 + 3.333333) / 3
    assert abs(result - expected) < 1e-6
    assert mock_func.call_count == 3


def test_avg_readings_function_exception():
    """Test avg_readings when the function raises an exception."""
    mock_func = Mock()
    mock_func.__name__ = "mock_sensor_function"
    mock_func.side_effect = Exception("Sensor failure")

    with pytest.raises(RuntimeError, match="Error retrieving reading from"):
        avg_readings(mock_func, num_readings=5)


def test_avg_readings_function_exception_on_second_call():
    """Test avg_readings when the function raises an exception on a later call."""
    mock_func = Mock()
    mock_func.__name__ = "mock_sensor_function"
    mock_func.side_effect = [
        Current(10.0),
        Current(20.0),
        Exception("Sensor failure on third reading"),
    ]

    with pytest.raises(RuntimeError, match="Error retrieving reading from"):
        avg_readings(mock_func, num_readings=5)

    # Should have tried 3 times before failing
    assert mock_func.call_count == 3


def test_avg_readings_function_name_in_error():
    """Test that the function name appears in the error message."""

    def test_sensor_func():
        """Mock sensor function that raises an error."""
        raise ValueError("Sensor error")

    with pytest.raises(
        RuntimeError, match="Error retrieving reading from test_sensor_func"
    ):
        avg_readings(test_sensor_func, num_readings=1)


def test_avg_readings_large_number_of_readings():
    """Test avg_readings with a large number of readings."""
    mock_func = Mock()
    mock_func.return_value = Current(1.0)

    result = avg_readings(mock_func, num_readings=1000)

    assert result == 1.0
    assert mock_func.call_count == 1000


def test_avg_readings_various_reading_counts():
    """Test avg_readings with various reading counts."""
    test_cases = [1, 2, 5, 10, 25, 50, 100]

    for count in test_cases:
        mock_func = Mock()
        mock_func.return_value = Voltage(2.5)

        result = avg_readings(mock_func, num_readings=count)

        assert result == 2.5
        assert mock_func.call_count == count
