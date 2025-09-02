"""Unit tests for the MicrocontrollerManager class.

This module contains unit tests for the `MicrocontrollerManager` class, which
manages the microcontroller's built-in Real-Time Clock (RTC). The tests cover
initialization and setting the time.
"""

import sys
import time
from unittest.mock import MagicMock

import pytest

# from mocks.circuitpython.rtc import RTC as MockRTC
MockRTC = MagicMock()
rtc = MagicMock()
rtc.RTC = MockRTC
sys.modules["rtc"] = rtc
from pysquared.rtc.manager.microcontroller import MicrocontrollerManager


@pytest.fixture(autouse=True)
def cleanup():
    """Cleans up the MockRTC instance after each test."""
    yield
    MockRTC().destroy()


def test_init():
    """Tests that the RTC.datetime is initialized with a time.struct_time.

    This test verifies that upon initialization of `MicrocontrollerManager`,
    the underlying mock RTC's `datetime` attribute is set to a `time.struct_time`
    instance, indicating proper setup.
    """
    MicrocontrollerManager()

    mrtc: MockRTC = MockRTC()
    assert mrtc.datetime is not None, "Mock RTC datetime should be set"
    assert isinstance(mrtc.datetime, time.struct_time), (
        "Mock RTC datetime should be a time.struct_time instance"
    )


def test_set_time():
    """Tests that the MicrocontrollerManager.set_time method correctly sets RTC.datetime.

    This test verifies that calling `set_time` on the `MicrocontrollerManager`
    updates the mock RTC's `datetime` attribute with the provided time components,
    and that the individual components of the `struct_time` match the input.
    """
    year = 2025
    month = 3
    day = 6
    hour = 10
    minute = 30
    second = 45
    day_of_week = 2

    # Set the time using the RP2040RTC class
    rtc = MicrocontrollerManager()
    rtc.set_time(year, month, day, hour, minute, second, day_of_week)

    # Get the mock RTC instance and check its datetime
    mrtc: MockRTC = MockRTC()
    assert mrtc.datetime is not None, "Mock RTC datetime should be set"
    assert isinstance(mrtc.datetime, time.struct_time), (
        "Mock RTC datetime should be a time.struct_time instance"
    )

    assert mrtc.datetime.tm_year == year, "Year should match"
    assert mrtc.datetime.tm_mon == month, "Month should match"
    assert mrtc.datetime.tm_mday == day, "Day should match"
    assert mrtc.datetime.tm_hour == hour, "Hour should match"
    assert mrtc.datetime.tm_min == minute, "Minute should match"
    assert mrtc.datetime.tm_sec == second, "Second should match"
    assert mrtc.datetime.tm_wday == day_of_week, "Day of week should match"
