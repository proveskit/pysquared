"""Unit tests for the ProvesMagnetorquerManager class.

This module contains unit tests for the `ProvesMagnetorquerManager` class, which manages
the PROVES V3 magnetorquer hardware using DRV2605L haptic motor drivers.
The tests cover initialization, dipole moment setting, error handling, and edge cases.
"""

from typing import Generator
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pysquared.hardware.exception import HardwareInitializationError
from pysquared.hardware.magnetorquer.manager.proves_magnetorquer import (
    ProvesMagnetorquerManager,
)


@pytest.fixture
def mock_i2c():
    """Fixture for mock I2C bus."""
    return MagicMock()


@pytest.fixture
def mock_logger():
    """Fixture for mock Logger."""
    return MagicMock()


@pytest.fixture
def mock_drv2605() -> Generator[MagicMock, None, None]:
    """Mocks the DRV2605 class.

    Yields:
        A MagicMock instance of DRV2605.
    """
    with patch(
        "pysquared.hardware.magnetorquer.manager.proves_magnetorquer.DRV2605"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_instance.mode = 0
        mock_instance.realtime_value = 0
        mock_class.return_value = mock_instance
        yield mock_class


def test_initialization_success(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests successful creation of a ProvesMagnetorquerManager instance.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(
        mock_logger,
        mock_i2c,
        addr_x_plus=0x5A,
        addr_x_minus=0x5B,
        addr_y_plus=0x5C,
        addr_y_minus=0x5D,
        addr_z_minus=0x5E,
    )

    # Verify that 5 DRV2605 instances were created
    assert mock_drv2605.call_count == 5

    # Verify that each was initialized with the correct I2C address
    mock_drv2605.assert_any_call(mock_i2c, 0x5A)
    mock_drv2605.assert_any_call(mock_i2c, 0x5B)
    mock_drv2605.assert_any_call(mock_i2c, 0x5C)
    mock_drv2605.assert_any_call(mock_i2c, 0x5D)
    mock_drv2605.assert_any_call(mock_i2c, 0x5E)

    # Verify that logger was called
    assert mock_logger.debug.call_count >= 1

    # Verify that manager has all driver instances
    assert manager._drv_x_plus is not None
    assert manager._drv_x_minus is not None
    assert manager._drv_y_plus is not None
    assert manager._drv_y_minus is not None
    assert manager._drv_z_minus is not None


def test_initialization_default_addresses(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests initialization with default I2C addresses.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Verify default addresses were used
    mock_drv2605.assert_any_call(mock_i2c, 0x5A)
    mock_drv2605.assert_any_call(mock_i2c, 0x5B)
    mock_drv2605.assert_any_call(mock_i2c, 0x5C)
    mock_drv2605.assert_any_call(mock_i2c, 0x5D)
    mock_drv2605.assert_any_call(mock_i2c, 0x5E)


def test_initialization_failure(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests that HardwareInitializationError is raised when DRV2605 initialization fails.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    mock_drv2605.side_effect = Exception("Simulated DRV2605 failure")

    # Verify that HardwareInitializationError is raised
    with pytest.raises(HardwareInitializationError) as excinfo:
        _ = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    assert "Failed to initialize magnetorquer DRV2605 drivers" in str(excinfo.value)


def test_set_dipole_moment_zero(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests setting zero dipole moment on all axes.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Set zero dipole moments - should not raise any errors
    manager.set_dipole_moment((0.0, 0.0, 0.0))

    # Verify no exceptions were raised
    assert True


def test_set_dipole_moment_positive_x(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests setting positive X-axis dipole moment.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Set small positive X dipole moment
    dipole = 0.0001  # A⋅m²
    manager.set_dipole_moment((dipole, 0.0, 0.0))

    # Verify no exceptions were raised
    assert True


def test_set_dipole_moment_negative_y(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests setting negative Y-axis dipole moment.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Set small negative Y dipole moment
    dipole = -0.0001  # A⋅m²
    manager.set_dipole_moment((0.0, dipole, 0.0))

    # Verify no exceptions were raised
    assert True


def test_set_dipole_moment_all_axes(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests setting dipole moment on all three axes simultaneously.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Set small dipole moments on all axes
    manager.set_dipole_moment((0.0001, -0.0001, 0.00005))

    # Verify no exceptions were raised
    assert True


def test_set_dipole_moment_exceeds_max_x(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests that ValueError is raised when X-axis dipole exceeds maximum.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Calculate maximum dipole moment for X-axis
    max_dipole = (
        manager._coil_max_current_x_y
        * manager._coil_num_turns_x_y
        * manager._coil_area_x_y
    )

    # Try to set dipole moment exceeding maximum
    with pytest.raises(ValueError) as excinfo:
        manager.set_dipole_moment((max_dipole * 1.1, 0.0, 0.0))

    assert "X-axis dipole moment" in str(excinfo.value)
    assert "exceeds maximum" in str(excinfo.value)


def test_set_dipole_moment_exceeds_max_y(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests that ValueError is raised when Y-axis dipole exceeds maximum.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Calculate maximum dipole moment for Y-axis
    max_dipole = (
        manager._coil_max_current_x_y
        * manager._coil_num_turns_x_y
        * manager._coil_area_x_y
    )

    # Try to set dipole moment exceeding maximum (negative direction)
    with pytest.raises(ValueError) as excinfo:
        manager.set_dipole_moment((0.0, -max_dipole * 1.1, 0.0))

    assert "Y-axis dipole moment" in str(excinfo.value)
    assert "exceeds maximum" in str(excinfo.value)


def test_set_dipole_moment_exceeds_max_z(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests that ValueError is raised when Z-axis dipole exceeds maximum.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Calculate maximum dipole moment for Z-axis
    max_dipole = (
        manager._coil_max_current_z * manager._coil_num_turns_z * manager._coil_area_z
    )

    # Try to set dipole moment exceeding maximum
    with pytest.raises(ValueError) as excinfo:
        manager.set_dipole_moment((0.0, 0.0, max_dipole * 1.1))

    assert "Z-axis dipole moment" in str(excinfo.value)
    assert "exceeds maximum" in str(excinfo.value)


def test_set_dipole_moment_communication_error(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests handling of communication errors when setting dipole moment.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Configure the property mock to raise an exception when set
    type(manager._drv_x_plus).realtime_value = PropertyMock(
        side_effect=Exception("I2C communication error")
    )

    # Verify that RuntimeError is raised
    with pytest.raises(RuntimeError) as excinfo:
        manager.set_dipole_moment((0.0001, 0.0, 0.0))

    assert "Failed to set magnetorquer dipole moment" in str(excinfo.value)


def test_dipole_to_current_conversion():
    """Tests the dipole to current conversion calculation."""
    # Test with known values
    dipole = 0.001  # A⋅m²
    num_turns = 48
    area = 0.002385  # m²

    current = ProvesMagnetorquerManager._dipole_to_current(dipole, num_turns, area)

    # Expected: I = dipole / (N * A) = 0.001 / (48 * 0.002385) ≈ 0.00874 A
    expected_current = dipole / (num_turns * area)
    assert abs(current - expected_current) < 1e-9


def test_dipole_to_current_zero():
    """Tests dipole to current conversion with zero dipole."""
    current = ProvesMagnetorquerManager._dipole_to_current(0.0, 48, 0.002385)
    assert current == 0.0


def test_current_to_drv_value_zero():
    """Tests current to DRV2605 value conversion with zero current."""
    max_current = 0.1  # A
    value = ProvesMagnetorquerManager._current_to_drv_value(0.0, max_current)
    assert value == 0


def test_current_to_drv_value_half():
    """Tests current to DRV2605 value conversion with half current."""
    max_current = 0.1  # A
    half_current = max_current / 2
    value = ProvesMagnetorquerManager._current_to_drv_value(half_current, max_current)
    assert 60 <= value <= 64  # Should be around 63


def test_current_to_drv_value_max():
    """Tests current to DRV2605 value conversion with maximum current."""
    max_current = 0.1  # A
    value = ProvesMagnetorquerManager._current_to_drv_value(max_current, max_current)
    assert value == 127


def test_current_to_drv_value_exceeds_max():
    """Tests current to DRV2605 value conversion with current exceeding maximum."""
    max_current = 0.1  # A
    value = ProvesMagnetorquerManager._current_to_drv_value(
        max_current * 2, max_current
    )
    assert value == 127  # Should clamp to 127


def test_current_to_drv_value_negative():
    """Tests current to DRV2605 value conversion with negative current."""
    max_current = 0.1  # A
    value = ProvesMagnetorquerManager._current_to_drv_value(-0.01, max_current)
    assert value == 0  # Should clamp to 0


def test_current_to_drv_value_zero_max_current():
    """Tests current to DRV2605 value conversion with zero max current."""
    value = ProvesMagnetorquerManager._current_to_drv_value(0.05, 0.0)
    assert value == 0  # Should handle division by zero gracefully


def test_set_axis_dipole_positive(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests _set_axis_dipole with positive dipole moment.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Create mock drivers
    drv_plus = MagicMock()
    drv_minus = MagicMock()

    # Set positive dipole
    manager._set_axis_dipole(0.0001, drv_plus, drv_minus, 48, 0.002385, 0.1, "Test")

    # Verify no exceptions were raised
    assert True


def test_set_axis_dipole_negative(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests _set_axis_dipole with negative dipole moment.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Create mock drivers
    drv_plus = MagicMock()
    drv_minus = MagicMock()

    # Set negative dipole
    manager._set_axis_dipole(-0.0001, drv_plus, drv_minus, 48, 0.002385, 0.1, "Test")

    # Verify no exceptions were raised
    assert True


def test_set_axis_dipole_zero(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests _set_axis_dipole with zero dipole moment.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Create mock drivers
    drv_plus = MagicMock()
    drv_minus = MagicMock()

    # Set zero dipole
    manager._set_axis_dipole(0.0, drv_plus, drv_minus, 48, 0.002385, 0.1, "Test")

    # Verify no exceptions were raised
    assert True


def test_set_axis_dipole_exceeds_max(
    mock_drv2605: MagicMock,
    mock_i2c: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Tests _set_axis_dipole raises ValueError when dipole exceeds maximum.

    Args:
        mock_drv2605: Mocked DRV2605 class.
        mock_i2c: Mocked I2C bus.
        mock_logger: Mocked Logger instance.
    """
    manager = ProvesMagnetorquerManager(mock_logger, mock_i2c)

    # Create mock drivers
    drv_plus = MagicMock()
    drv_minus = MagicMock()

    # Calculate maximum dipole
    num_turns = 48
    area = 0.002385
    max_current = 0.1
    max_dipole = max_current * num_turns * area

    # Try to set dipole exceeding maximum
    with pytest.raises(ValueError) as excinfo:
        manager._set_axis_dipole(
            max_dipole * 1.1, drv_plus, drv_minus, num_turns, area, max_current, "Test"
        )

    assert "Test-axis dipole moment" in str(excinfo.value)
    assert "exceeds maximum" in str(excinfo.value)


def test_coil_constants():
    """Tests that coil constants are properly defined and calculated."""
    # Verify X/Y coil constants
    assert ProvesMagnetorquerManager._coil_voltage == 3.3
    assert ProvesMagnetorquerManager._coil_num_turns_x_y == 48
    assert ProvesMagnetorquerManager._coil_length_x_y == 0.053
    assert ProvesMagnetorquerManager._coil_width_x_y == 0.045
    assert (
        ProvesMagnetorquerManager._coil_area_x_y
        == ProvesMagnetorquerManager._coil_length_x_y
        * ProvesMagnetorquerManager._coil_width_x_y
    )
    assert ProvesMagnetorquerManager._coil_resistance_x_y == 57.2
    assert (
        ProvesMagnetorquerManager._coil_max_current_x_y
        == ProvesMagnetorquerManager._coil_voltage
        / ProvesMagnetorquerManager._coil_resistance_x_y
    )

    # Verify Z coil constants
    assert ProvesMagnetorquerManager._coil_num_turns_z == 153
    assert ProvesMagnetorquerManager._coil_diameter_z == 0.05755
    assert ProvesMagnetorquerManager._coil_resistance_z == 248.8
    assert (
        ProvesMagnetorquerManager._coil_max_current_z
        == ProvesMagnetorquerManager._coil_voltage
        / ProvesMagnetorquerManager._coil_resistance_z
    )

    # Verify Z coil area calculation
    import math

    expected_area_z = math.pi * (ProvesMagnetorquerManager._coil_diameter_z / 2) ** 2
    assert abs(ProvesMagnetorquerManager._coil_area_z - expected_area_z) < 1e-9
