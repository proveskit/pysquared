import sys
from unittest.mock import Mock

# Mock CircuitPython modules globally for all tests
sys.modules["alarm"] = Mock()
sys.modules["alarm.time"] = Mock()
sys.modules["alarm.time.TimeAlarm"] = Mock()
sys.modules["microcontroller"] = Mock()
sys.modules["pysquared.satellite"] = Mock()
