from unittest.mock import MagicMock, patch

import pytest
from microcontroller import Pin

from pysquared.hardware.busio import initialize_i2c_bus, initialize_spi_bus
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.logger import Logger


@patch("pysquared.hardware.busio.SPI")
def test_initialize_spi_bus_success(mock_spi: MagicMock):
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pins
    mock_clock = MagicMock(spec=Pin)
    mock_mosi = MagicMock(spec=Pin)
    mock_miso = MagicMock(spec=Pin)

    # Mock SPI instance
    mock_spi_instance = mock_spi.return_value

    # Test parameters
    baudrate = 200000
    phase = 1
    polarity = 1
    bits = 16

    # Call fn under test
    result = initialize_spi_bus(
        mock_logger, mock_clock, mock_mosi, mock_miso, baudrate, phase, polarity, bits
    )

    # Assertions
    mock_spi.assert_called_once_with(mock_clock, mock_mosi, mock_miso)
    mock_spi_instance.try_lock.assert_called_once()
    mock_spi_instance.configure.assert_called_once_with(baudrate, phase, polarity, bits)
    mock_spi_instance.unlock.assert_called_once()
    assert mock_logger.debug.call_count == 2
    assert result == mock_spi_instance


@patch("pysquared.hardware.busio.SPI")
def test_initialize_spi_bus_failure(mock_spi: MagicMock):
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pins
    mock_clock = MagicMock(spec=Pin)
    mock_mosi = MagicMock(spec=Pin)
    mock_miso = MagicMock(spec=Pin)

    # Mock SPI to raise an exception
    mock_spi.side_effect = Exception("Simulated failure")

    # Call the function and assert exception
    with pytest.raises(HardwareInitializationError):
        initialize_spi_bus(mock_logger, mock_clock, mock_mosi, mock_miso)

    # Assertions
    assert mock_spi.call_count == 1
    mock_logger.debug.assert_called_with("Initializing spi bus")


@patch("pysquared.hardware.busio.SPI")
def test_spi_bus_configure_try_lock_failure(mock_spi: MagicMock):
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pins
    mock_clock = MagicMock(spec=Pin)
    mock_mosi = MagicMock(spec=Pin)
    mock_miso = MagicMock(spec=Pin)

    # Mock SPI.try_lock() to return false
    mock_spi_instance = mock_spi.return_value
    mock_spi_instance.try_lock.return_value = False

    # Call the function and assert exception
    with pytest.raises(HardwareInitializationError):
        initialize_spi_bus(mock_logger, mock_clock, mock_mosi, mock_miso)

    # Assertions
    assert (
        mock_spi_instance.try_lock.call_count == 201
    )  # Called 200 times due to retries
    mock_logger.debug.assert_called_with("Configuring spi bus")


@patch("pysquared.hardware.busio.SPI")
def test_spi_bus_configure_failure(mock_spi: MagicMock):
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pins
    mock_clock = MagicMock(spec=Pin)
    mock_mosi = MagicMock(spec=Pin)
    mock_miso = MagicMock(spec=Pin)

    # Mock SPI.try_lock() to return false
    mock_spi_instance = mock_spi.return_value
    mock_spi_instance.try_lock.return_value = True
    mock_spi_instance.configure.side_effect = Exception("Simulated failure")

    # Call the function and assert exception
    with pytest.raises(HardwareInitializationError):
        initialize_spi_bus(mock_logger, mock_clock, mock_mosi, mock_miso)

    # Assertions
    mock_spi_instance.try_lock.assert_called_once()
    mock_spi_instance.configure.assert_called_once()
    mock_spi_instance.unlock.assert_called_once()
    mock_logger.debug.assert_called_with("Configuring spi bus")


@patch("pysquared.hardware.busio.I2C")
def test_initialize_i2c_bus_success(mock_i2c: MagicMock):
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pins
    mock_scl = MagicMock(spec=Pin)
    mock_sda = MagicMock(spec=Pin)

    # Mock I2C instance
    mock_i2c_instance = mock_i2c.return_value

    # Test parameters
    frequency = 200000

    # Call fn under test
    result = initialize_i2c_bus(mock_logger, mock_scl, mock_sda, frequency)

    # Assertions
    mock_i2c.assert_called_once_with(mock_scl, mock_sda, frequency=frequency)
    mock_logger.debug.assert_called_once()
    assert result == mock_i2c_instance


@patch("pysquared.hardware.busio.I2C")
def test_initialize_i2c_bus_failure(mock_i2c: MagicMock):
    # Mock the logger
    mock_logger = MagicMock(spec=Logger)

    # Mock pins
    mock_scl = MagicMock(spec=Pin)
    mock_sda = MagicMock(spec=Pin)

    # Mock I2C instance to raise an exception
    mock_i2c.side_effect = Exception("Simulated failure")

    # Call the function and assert exception
    with pytest.raises(HardwareInitializationError):
        initialize_i2c_bus(mock_logger, mock_scl, mock_sda)

    # Assertions
    assert mock_i2c.call_count == 1
    mock_logger.debug.assert_called()
