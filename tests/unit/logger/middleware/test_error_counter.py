"""Unit tests for the Logger class.

This module contains unit tests for the `Logger` class, which provides logging
functionality with different severity levels, colorized output, and error counting.
"""

from unittest.mock import MagicMock

import pytest

import pysquared.nvm.counter as counter
from pysquared.logger.default_logger import DefaultLogger
from pysquared.logger.middleware.error_counter.error_counter import (
    add_logger_middleware_error_counter,
)


@pytest.fixture
def logger():
    """Provides a Logger instance for testing without colorization."""
    count = MagicMock(spec=counter.Counter)
    logger = DefaultLogger(count)
    return add_logger_middleware_error_counter(count)(logger)


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

    logger._counter.increment.assert_not_called()


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

    logger._counter.increment.assert_not_called()


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

    logger._counter.increment.assert_not_called()


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

    logger._counter.increment.assert_called_once()


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

    logger._counter.increment.assert_called_once()
