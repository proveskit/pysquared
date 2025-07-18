"""Unit tests for the Logger class.

This module contains unit tests for the `Logger` class, which provides logging
functionality with different severity levels, colorized output, and error counting.
"""

from unittest.mock import MagicMock

import pytest
from microcontroller import Pin

import pysquared.nvm.counter as counter
from pysquared.logger import Logger, _color


@pytest.fixture
def logger():
    """Provides a Logger instance for testing without colorization."""
    count = MagicMock(spec=counter.Counter)
    return Logger(count)


@pytest.fixture
def logger_color():
    """Provides a Logger instance for testing with colorization enabled."""
    count = MagicMock(spec=counter.Counter)
    return Logger(error_counter=count, colorized=True)


def test_debug_log(capsys, logger):
    """Tests logging a debug message without colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    logger.debug("This is a debug message", blake="jameson")
    captured = capsys.readouterr()
    assert "DEBUG" in captured.out
    assert "This is a debug message" in captured.out
    assert '"blake": "jameson"' in captured.out


def test_debug_with_err(capsys, logger):
    """Tests logging a debug message with an error object without colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    logger.debug(
        "This is another debug message", err=OSError("Manually creating an OS Error")
    )
    captured = capsys.readouterr()
    assert "DEBUG" in captured.out
    assert "This is another debug message" in captured.out
    assert "OSError: Manually creating an OS Error" in captured.out


def test_info_log(capsys, logger):
    """Tests logging an info message without colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    logger.info(
        "This is a info message!!",
        foo="bar",
    )
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "This is a info message!!" in captured.out
    assert '"foo": "bar"' in captured.out


def test_info_with_err(capsys, logger):
    """Tests logging an info message with an error object without colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    logger.info(
        "This is a info message!!",
        foo="barrrr",
        err=OSError("Manually creating an OS Error"),
    )
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "This is a info message!!" in captured.out
    assert '"foo": "barrrr"' in captured.out
    assert "OSError: Manually creating an OS Error" in captured.out


def test_warning_log(capsys, logger):
    """Tests logging a warning message without colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    logger.warning(
        "This is a warning message!!??!",
        boo="bar",
        pleiades="maia",
        cube="sat",
        err=Exception("manual exception"),
    )
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "This is a warning message!!??!" in captured.out
    assert '"boo": "bar"' in captured.out
    assert '"pleiades": "maia"' in captured.out
    assert '"cube": "sat"' in captured.out
    assert "Exception: manual exception" in captured.out


def test_error_log(capsys, logger):
    """Tests logging an error message without colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    logger.error(
        "This is an error message",
        OSError("Manually creating an OS Error for testing"),
        pleiades="five",
        please="work",
    )
    captured = capsys.readouterr()
    assert "ERROR" in captured.out
    assert "This is an error message" in captured.out
    assert '"pleiades": "five"' in captured.out
    assert '"please": "work"' in captured.out
    assert "OSError: Manually creating an OS Error for testing" in captured.out


def test_critical_log(capsys, logger):
    """Tests logging a critical message without colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    logger.critical(
        "THIS IS VERY CRITICAL",
        OSError("Manually creating an OS Error"),
        ad="astra",
        space="lab",
        soft="ware",
        j="20",
        config="king",
    )
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.out
    assert "THIS IS VERY CRITICAL" in captured.out
    assert '"ad": "astra"' in captured.out
    assert '"space": "lab"' in captured.out
    assert '"soft": "ware"' in captured.out
    assert '"j": "20"' in captured.out
    assert '"config": "king"' in captured.out


def test_debug_log_color(capsys, logger_color):
    """Tests logging a debug message with colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger_color: Colorized Logger instance for testing.
    """
    logger_color.debug("This is a debug message", blake="jameson")
    captured = capsys.readouterr()
    assert _color(msg="DEBUG", color="blue") in captured.out
    assert "This is a debug message" in captured.out
    assert '"blake": "jameson"' in captured.out


def test_info_log_color(capsys, logger_color):
    """Tests logging an info message with colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger_color: Colorized Logger instance for testing.
    """
    logger_color.info("This is a info message!!", foo="bar")
    captured = capsys.readouterr()
    assert _color(msg="INFO", color="green") in captured.out
    assert "This is a info message!!" in captured.out
    assert '"foo": "bar"' in captured.out


def test_warning_log_color(capsys, logger_color):
    """Tests logging a warning message with colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger_color: Colorized Logger instance for testing.
    """
    logger_color.warning(
        "This is a warning message!!??!", boo="bar", pleiades="maia", cube="sat"
    )
    captured = capsys.readouterr()
    assert _color(msg="WARNING", color="orange") in captured.out
    assert "This is a warning message!!??!" in captured.out
    assert '"boo": "bar"' in captured.out
    assert '"pleiades": "maia"' in captured.out
    assert '"cube": "sat"' in captured.out


def test_error_log_color(capsys, logger_color):
    """Tests logging an error message with colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger_color: Colorized Logger instance for testing.
    """
    logger_color.error(
        "This is an error message",
        pleiades="five",
        please="work",
        err=OSError("Manually creating an OS Error"),
    )
    captured = capsys.readouterr()
    assert _color(msg="ERROR", color="pink") in captured.out
    assert "This is an error message" in captured.out
    assert '"pleiades": "five"' in captured.out
    assert '"please": "work"' in captured.out


def test_critical_log_color(capsys, logger_color):
    """Tests logging a critical message with colorization.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger_color: Colorized Logger instance for testing.
    """
    logger_color.critical(
        "THIS IS VERY CRITICAL",
        ad="astra",
        space="lab",
        soft="ware",
        j="20",
        config="king",
        err=OSError("Manually creating an OS Error"),
    )
    captured = capsys.readouterr()
    assert _color(msg="CRITICAL", color="red") in captured.out
    assert "THIS IS VERY CRITICAL" in captured.out
    assert '"ad": "astra"' in captured.out
    assert '"space": "lab"' in captured.out
    assert '"soft": "ware"' in captured.out
    assert '"j": "20"' in captured.out
    assert '"config": "king"' in captured.out


# testing a kwarg of value type bytes, which previously caused a TypeError exception
def test_invalid_json_type_bytes(capsys, logger):
    """Tests logging with a bytes type keyword argument.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    byte_message = b"forming a bytes message"
    logger.debug("This is a random message", attempt=byte_message)
    captured = capsys.readouterr()
    assert "b'forming a bytes message'" in captured.out
    assert "TypeError" not in captured.out


# testing a kwarg of value type Pin, which previously caused a TypeError exception
def test_invalid_json_type_pin(capsys, logger):
    """Tests logging with a Pin type keyword argument.

    Args:
        capsys: Pytest fixture to capture stdout/stderr.
        logger: Logger instance for testing.
    """
    mock_pin = MagicMock(spec=Pin)
    logger.debug("Initializing watchdog", pin=mock_pin)
    captured = capsys.readouterr()
    assert "TypeError" not in captured.out
