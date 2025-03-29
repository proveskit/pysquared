import time

import pytest

import mocks.circuitpython.rtc as MockRTC
from pysquared.rtc.microcontroller.factory import MicrocontrollerFactory


@pytest.fixture(autouse=True)
def cleanup():
    yield
    MockRTC.RTC().destroy()


def test_init():
    """Test that the RTC.datetime is initialized with a time.struct_time"""
    MicrocontrollerFactory()

    mrtc: MockRTC = MockRTC.RTC()
    assert mrtc.datetime is not None, "Mock RTC datetime should be set"
    assert isinstance(
        mrtc.datetime, time.struct_time
    ), "Mock RTC datetime should be a time.struct_time instance"


def test_set_time():
    """Test that the RP2040RTCFactory.set_time method correctly sets RTC.datetime"""
    year = 2025
    month = 3
    day = 6
    hour = 10
    minute = 30
    second = 45
    day_of_week = 2

    # Set the time using the RP2040RTC class
    rtc = MicrocontrollerFactory()
    rtc.set_time(year, month, day, hour, minute, second, day_of_week)

    # Get the mock RTC instance and check its datetime
    mrtc: MockRTC = MockRTC.RTC()
    assert mrtc.datetime is not None, "Mock RTC datetime should be set"
    assert isinstance(
        mrtc.datetime, time.struct_time
    ), "Mock RTC datetime should be a time.struct_time instance"

    assert mrtc.datetime.tm_year == year, "Year should match"
    assert mrtc.datetime.tm_mon == month, "Month should match"
    assert mrtc.datetime.tm_mday == day, "Day should match"
    assert mrtc.datetime.tm_hour == hour, "Hour should match"
    assert mrtc.datetime.tm_min == minute, "Minute should match"
    assert mrtc.datetime.tm_sec == second, "Second should match"
    assert mrtc.datetime.tm_wday == day_of_week, "Day of week should match"
