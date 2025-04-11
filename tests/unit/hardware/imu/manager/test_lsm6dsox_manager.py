import math
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from mocks.adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.imu.manager.lsm6dsox import LSM6DSOXManager

# Type hinting only
try:
    from busio import I2C

    from pysquared.logger import Logger
except ImportError:
    pass


@pytest.fixture
def mock_i2c() -> MagicMock:
    """Fixture for mock I2C bus."""
    return MagicMock(spec=I2C)


@pytest.fixture
def mock_logger() -> MagicMock:
    """Fixture for mock Logger."""
    return MagicMock(spec=Logger)


address: int = 0x6A


def test_create_imu(mock_i2c: MagicMock, mock_logger: MagicMock) -> None:
    """Test successful creation of an LSM6DSOX IMU instance."""
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)

    assert isinstance(imu_manager._imu, LSM6DSOX)
    mock_logger.debug.assert_called_once_with("Initializing IMU")


@patch("pysquared.hardware.imu.manager.lsm6dsox.LSM6DSOX")
def test_create_error(
    mock_lsm6dsox: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test that initialization is retried when it fails."""
    mock_lsm6dsox.side_effect = Exception("Simulated LSM6DSOX failure")

    with pytest.raises(HardwareInitializationError):
        _ = LSM6DSOXManager(mock_logger, mock_i2c, address)

    mock_logger.debug.assert_called_with("Initializing IMU")
    assert mock_lsm6dsox.call_count == 1


def test_get_acceleration_success(
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test successful retrieval of the acceleration vector."""
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    # Replace the automatically created mock instance with a MagicMock we can configure
    imu_manager._imu = MagicMock(spec=LSM6DSOX)
    expected_accel = (1.0, 2.0, 9.8)
    imu_manager._imu.acceleration = expected_accel

    vector = imu_manager.get_acceleration()
    assert vector == expected_accel


def test_get_acceleration_failure(
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test handling of exceptions when retrieving the acceleration vector."""
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
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test successful retrieval of the gyro vector."""
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    imu_manager._imu = MagicMock(spec=LSM6DSOX)
    expected_gyro = (0.1, 0.2, 0.3)
    imu_manager._imu.gyro = expected_gyro

    vector = imu_manager.get_gyro_data()
    assert vector == expected_gyro


def test_get_gyro_failure(
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test handling of exceptions when retrieving the gyro vector."""
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
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test successful retrieval of the temperature."""
    imu_manager = LSM6DSOXManager(mock_logger, mock_i2c, address)
    imu_manager._imu = MagicMock(spec=LSM6DSOX)
    expected_temp = 25.5
    imu_manager._imu.temperature = expected_temp

    temp = imu_manager.get_temperature()
    assert math.isclose(temp, expected_temp, rel_tol=1e-9)


def test_get_temperature_failure(mock_i2c: MagicMock, mock_logger: MagicMock) -> None:
    """Test handling of exceptions when retrieving the temperature."""
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
