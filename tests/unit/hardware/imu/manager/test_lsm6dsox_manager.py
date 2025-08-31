"""Unit tests for the LSM6DSOXManager class.

This module contains unit tests for the `LSM6DSOXManager` class, which manages
the LSM6DSOX IMU. The tests cover initialization, successful data retrieval,
and error handling for acceleration, gyroscope, and temperature readings.
"""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportReturnType=false

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from busio import I2C

from mocks.adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.imu.manager.lsm6dsox import LSM6DSOXManager
from pysquared.logger import Logger

address: int = 123


@pytest.fixture
def mock_i2c() -> MagicMock:
    """Fixture for mock I2C bus."""
    return MagicMock(spec=I2C)


@pytest.fixture
def mock_logger() -> MagicMock:
    """Fixture for mock Logger."""
    return MagicMock(spec=Logger)


@pytest.fixture
def mock_lsm6dsox(mock_i2c: I2C) -> Generator[MagicMock, None, None]:
    """Mocks the LSM6DSOX class.

    Args:
        mock_i2c: Mocked I2C bus.

    Yields:
        A MagicMock instance of LSM6DSOX.
    """
    with patch("pysquared.hardware.imu.manager.lsm6dsox.LSM6DSOX") as mock_class:
        mock_class.return_value = LSM6DSOX(mock_i2c, address)
        yield mock_class


def test_create_imu(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger,
) -> None:
    """Tests successful creation of an LSM6DSOX IMU instance.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)

    assert isinstance(imu_manager._imu, LSM6DSOX)
    mock_logger.debug.assert_called_once_with("Initializing IMU")


def test_create_imu_failed(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger,
) -> None:
    """Tests that initialization is retried when it fails.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_lsm6dsox.side_effect = Exception("Simulated LSM6DSOX failure")

    with pytest.raises(HardwareInitializationError):
        _ = LSM6DSOXManager(mock_logger, mock_i2c, address)

    mock_logger.debug.assert_called_with("Initializing IMU")
    mock_lsm6dsox.assert_called_once()


def test_get_acceleration_success(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger: Logger,
) -> None:
    """Tests successful retrieval of the acceleration vector.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    # Replace the automatically created mock instance with a MagicMock we can configure
    imu_manager._imu = MagicMock(spec=LSM6DSOX)
    expected_accel = (1.0, 2.0, 9.8)
    imu_manager._imu.acceleration = expected_accel

    vector = imu_manager.get_acceleration()
    assert vector == expected_accel


def test_get_acceleration_failure(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger,
) -> None:
    """Tests handling of exceptions when retrieving the acceleration vector.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    mock_imu_instance = MagicMock(spec=LSM6DSOX)
    imu_manager._imu = mock_imu_instance

    # Configure the mock to raise an exception when accessing the acceleration property
    mock_accel_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(mock_imu_instance).acceleration = mock_accel_property

    vector = imu_manager.get_acceleration()

    assert vector is None
    assert mock_logger.error.call_count == 1
    call_args, _ = mock_logger.error.call_args
    assert call_args[0] == "Error retrieving IMU acceleration sensor values"
    assert isinstance(call_args[1], RuntimeError)
    assert str(call_args[1]) == "Simulated retrieval error"


def test_get_gyro_success(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger: Logger,
) -> None:
    """Tests successful retrieval of the gyro vector.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    imu_manager._imu = MagicMock(spec=LSM6DSOX)
    expected_gyro = (0.1, 0.2, 0.3)
    imu_manager._imu.gyro = expected_gyro

    vector = imu_manager.get_gyro_data()
    assert vector == expected_gyro


def test_get_gyro_failure(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger,
) -> None:
    """Tests handling of exceptions when retrieving the gyro vector.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    mock_imu_instance = MagicMock(spec=LSM6DSOX)
    imu_manager._imu = mock_imu_instance

    mock_gyro_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(mock_imu_instance).gyro = mock_gyro_property

    vector = imu_manager.get_gyro_data()

    assert vector is None
    assert mock_logger.error.call_count == 1
    call_args, _ = mock_logger.error.call_args
    assert call_args[0] == "Error retrieving IMU gyro sensor values"
    assert isinstance(call_args[1], RuntimeError)
    assert str(call_args[1]) == "Simulated retrieval error"


def test_get_temperature_success(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger: Logger,
) -> None:
    """Tests successful retrieval of the temperature.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    imu_manager._imu = MagicMock(spec=LSM6DSOX)
    expected_temp = 25.5
    imu_manager._imu.temperature = expected_temp

    temp = imu_manager.get_temperature()
    assert temp is not None
    assert pytest.approx(expected_temp, rel=1e-9) == temp


def test_get_temperature_failure(
    mock_lsm6dsox: MagicMock,
    mock_i2c: I2C,
    mock_logger,
) -> None:
    """Tests handling of exceptions when retrieving the temperature.

    Args:
        mock_lsm6dsox: Mocked LSM6DSOX class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    mock_imu_instance = MagicMock(spec=LSM6DSOX)
    imu_manager._imu = mock_imu_instance

    mock_temp_property = PropertyMock(
        side_effect=RuntimeError("Simulated retrieval error")
    )
    type(mock_imu_instance).temperature = mock_temp_property

    temp = imu_manager.get_temperature()

    assert temp is None
    assert mock_logger.error.call_count == 1
    call_args, _ = mock_logger.error.call_args
    assert call_args[0] == "Error retrieving IMU temperature sensor values"
    assert isinstance(call_args[1], RuntimeError)
    assert str(call_args[1]) == "Simulated retrieval error"
