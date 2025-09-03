"""Unit tests for the filesystem class.

This file contains unit tests for the `filesystem` class, which provides utilities
for managing the filesystem during the boot process. The tests focus on verifying that
the correct sequence of filesystem operations.
"""

import os
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.modules["storage"] = MagicMock()
from pysquared.boot.filesystem import mkdir  # noqa: E402


@pytest.fixture(autouse=True)
def test_dir():
    """Sets up a temporary directory for testing and cleans it up afterwards."""
    temp_dir = tempfile.mkdtemp()

    test_dir = os.path.join(temp_dir, "mytestdir")
    yield test_dir

    shutil.rmtree(temp_dir, ignore_errors=True)


@patch("pysquared.boot.filesystem.storage")
@patch("pysquared.boot.filesystem.time.sleep")
def test_mkdir_success(
    mock_sleep: MagicMock,
    mock_storage: MagicMock,
    test_dir: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the mkdir function for successful directory creation."""
    mkdir(test_dir, 0.02)

    # Verify each expected call was made
    mock_storage.disable_usb_drive.assert_called_once()
    mock_storage.remount.assert_called_once_with("/", False)
    mock_storage.enable_usb_drive.assert_called_once()

    assert mock_sleep.call_count == 3
    mock_sleep.assert_called_with(0.02)

    # Verify correct print messages
    captured = capsys.readouterr()
    assert "Disabled USB drive" in captured.out
    assert "Remounted root filesystem" in captured.out
    assert f"Mount point {test_dir} created." in captured.out
    assert "Enabled USB drive" in captured.out

    # directory exists
    assert os.path.exists(test_dir)


@patch("pysquared.boot.filesystem.storage")
@patch("pysquared.boot.filesystem.time.sleep")
@patch("pysquared.boot.filesystem.os.mkdir")
def test_mkdir_directory_already_exists(
    mock_os_mkdir: MagicMock,
    mock_sleep: MagicMock,
    mock_storage: MagicMock,
    test_dir: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the mkdir function when directory already exists."""
    mock_os_mkdir.side_effect = OSError("Directory already exists")

    mkdir(test_dir, 0.02)

    # Verify all storage operations still performed
    mock_storage.disable_usb_drive.assert_called_once()
    mock_storage.remount.assert_called_once_with("/", False)
    mock_os_mkdir.assert_called_once_with(test_dir)
    mock_storage.enable_usb_drive.assert_called_once()

    # Verify correct print messages
    captured = capsys.readouterr()
    assert "Disabled USB drive" in captured.out
    assert "Remounted root filesystem" in captured.out
    assert f"Mount point {test_dir} already exists." in captured.out
    assert "Enabled USB drive" in captured.out


@patch("pysquared.boot.filesystem.storage")
@patch("pysquared.boot.filesystem.time.sleep")
@patch("pysquared.boot.filesystem.os.mkdir")
def test_mkdir_custom_delay(
    mock_os_mkdir: MagicMock,
    mock_sleep: MagicMock,
    mock_storage: MagicMock,
    test_dir: str,
) -> None:
    """Test the mkdir function with custom storage action delay."""
    custom_delay = 0.05
    mkdir(test_dir, custom_delay)

    # Verify sleep was called with custom delay
    assert mock_sleep.call_count == 3
    mock_sleep.assert_called_with(custom_delay)


@patch("pysquared.boot.filesystem.storage")
@patch("pysquared.boot.filesystem.time.sleep")
@patch("pysquared.boot.filesystem.os.mkdir")
def test_mkdir_default_delay(
    mock_os_mkdir: MagicMock,
    mock_sleep: MagicMock,
    mock_storage: MagicMock,
    test_dir: str,
) -> None:
    """Test the mkdir function with default storage action delay."""
    mkdir(test_dir)  # No delay parameter provided

    # Verify sleep was called with default delay
    assert mock_sleep.call_count == 3
    mock_sleep.assert_called_with(0.02)


@patch("pysquared.boot.filesystem.storage")
@patch("pysquared.boot.filesystem.time.sleep")
@patch("pysquared.boot.filesystem.os.mkdir")
def test_mkdir_storage_disable_exception(
    mock_os_mkdir: MagicMock,
    mock_sleep: MagicMock,
    mock_storage: MagicMock,
    test_dir: str,
) -> None:
    """Test mkdir function when storage.disable_usb_drive() raises an exception."""
    mock_storage.disable_usb_drive.side_effect = Exception("USB disable failed")

    with pytest.raises(Exception, match="USB disable failed"):
        mkdir(test_dir, 0.02)

    # Verify that enable_usb_drive is still called in finally block
    mock_storage.enable_usb_drive.assert_called_once()


@patch("pysquared.boot.filesystem.storage")
@patch("pysquared.boot.filesystem.time.sleep")
def test_mkdir_storage_remount_exception(
    mock_sleep: MagicMock,
    mock_storage: MagicMock,
    test_dir: str,
) -> None:
    """Test mkdir function when storage.remount() raises an exception."""
    mock_storage.remount.side_effect = Exception("Remount failed")

    with pytest.raises(Exception, match="Remount failed"):
        mkdir(test_dir, 0.02)

    # Verify that enable_usb_drive is still called in finally block
    mock_storage.enable_usb_drive.assert_called_once()


@patch("pysquared.boot.filesystem.storage")
@patch("pysquared.boot.filesystem.time.sleep")
@patch("pysquared.boot.filesystem.os.mkdir")
def test_mkdir_mkdir_exception_not_oserror(
    mock_os_mkdir: MagicMock,
    mock_sleep: MagicMock,
    mock_storage: MagicMock,
    test_dir: str,
) -> None:
    """Test mkdir function when os.mkdir() raises a non-OSError exception."""
    mock_os_mkdir.side_effect = ValueError("Invalid path")

    with pytest.raises(ValueError, match="Invalid path"):
        mkdir(test_dir, 0.02)

    # Verify that enable_usb_drive is still called in finally block
    mock_storage.enable_usb_drive.assert_called_once()
