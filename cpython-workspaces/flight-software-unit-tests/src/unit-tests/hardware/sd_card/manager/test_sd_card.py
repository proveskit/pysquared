"""Unit tests for the filesystem class.

This file contains unit tests for the `filesystem` class, which provides utilities
for managing the filesystem during the boot process. The tests focus on verifying that
the correct sequence of filesystem operations.
"""

# pyright: reportAttributeAccessIssue=false

import sys
from unittest.mock import MagicMock, patch

import pytest
from busio import SPI
from microcontroller import Pin
from pysquared.hardware.exception import HardwareInitializationError

sys.modules["storage"] = MagicMock()
sys.modules["sdcardio"] = MagicMock()

from pysquared.hardware.sd_card.manager.sd_card import SDCardManager  # noqa: E402


@patch("pysquared.hardware.sd_card.manager.sd_card.storage")
@patch("pysquared.hardware.sd_card.manager.sd_card.sdcardio")
def test_sdcard_init_success(
    mock_sdcardio: MagicMock,
    mock_storage: MagicMock,
) -> None:
    """Test SD Card successful initialization."""
    mock_sd_card = MagicMock()
    mock_sdcardio.SDCard.return_value = mock_sd_card

    mock_block_device = MagicMock()
    mock_storage.VfsFat.return_value = mock_block_device

    spi = MagicMock(spec=SPI)
    cs = MagicMock(spec=Pin)
    baudrate = 400000
    mount_path = "/sd"
    _ = SDCardManager(
        spi_bus=spi,
        chip_select=cs,
        baudrate=baudrate,
        mount_path=mount_path,
    )

    # Verify each expected call was made
    mock_sdcardio.SDCard.assert_called_once_with(spi, cs, baudrate)
    mock_storage.VfsFat.assert_called_once_with(mock_sd_card)
    mock_storage.mount.assert_called_once_with(mock_block_device, mount_path)


@patch("pysquared.hardware.sd_card.manager.sd_card.storage")
@patch("pysquared.hardware.sd_card.manager.sd_card.sdcardio")
def test_sdcard_init_error(
    mock_sdcardio: MagicMock,
    mock_storage: MagicMock,
) -> None:
    """Test SD Card failing initialization"""
    mock_sdcardio.SDCard.side_effect = Exception("Evan (SD) Ortiz")

    with pytest.raises(
        HardwareInitializationError, match="Failed to initialize SD Card"
    ):
        _ = SDCardManager(
            spi_bus=MagicMock(spec=SPI),
            chip_select=MagicMock(spec=Pin),
            baudrate=400000,
            mount_path="/sd",
        )
