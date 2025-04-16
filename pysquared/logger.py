"""
Logger class for handling logging messages with different severity levels.
Logs can be output to standard output or saved to a file (functionality to be implemented).
"""

import json
import time
import traceback
from collections import OrderedDict

from pysquared.sdcard.manager import log_to_sd

from .nvm.counter import Counter


def _color(msg, color="gray", fmt="normal"):
    _h = "\033["
    _e = "\033[0;39;49m"

    _c = {
        "red": "1",
        "green": "2",
        "orange": "3",
        "blue": "4",
        "pink": "5",
        "teal": "6",
        "white": "7",
        "gray": "9",
    }

    _f = {"normal": "0", "bold": "1", "ulined": "4"}
    return _h + _f[fmt] + ";3" + _c[color] + "m" + msg + _e


LogColors = {
    "NOTSET": "NOTSET",
    "DEBUG": _color(msg="DEBUG", color="blue"),
    "INFO": _color(msg="INFO", color="green"),
    "WARNING": _color(msg="WARNING", color="orange"),
    "ERROR": _color(msg="ERROR", color="pink"),
    "CRITICAL": _color(msg="CRITICAL", color="red"),
}


class LogLevel:
    NOTSET = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class Logger:
    def __init__(
        self,
        error_counter: Counter,
        log_level: int = LogLevel.NOTSET,
        colorized: bool = False,
        sd_log: bool = False,
    ) -> None:
        self._error_counter: Counter = error_counter
        self._log_level: int = log_level
        self.colorized: bool = colorized
        self.sd_log: bool = sd_log

    def _can_print_this_level(self, level_value: int) -> bool:
        return level_value >= self._log_level

    def _is_valid_json_type(self, object) -> bool:
        valid_types = {dict, list, tuple, str, int, float, bool, None}

        return type(object) in valid_types

    def _log(self, level: str, level_value: int, message: str, **kwargs) -> None:
        """
        Log a message with a given severity level and any addional key/values.
        """
        now = time.localtime()
        asctime = f"{now.tm_year}-{now.tm_mon:02d}-{now.tm_mday:02d} {now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"

        # case where someone used debug, info, or warning yet also provides an 'err' kwarg with an Exception
        if (
            "err" in kwargs
            and level not in ("ERROR", "CRITICAL")
            and isinstance(kwargs["err"], Exception)
        ):
            kwargs["err"] = traceback.format_exception(kwargs["err"])

        json_order: OrderedDict[str, str] = OrderedDict(
            [("time", asctime), ("level", level), ("msg", message)]
        )

        # detect if there are kwargs with invalid types (would cause TypeError) and converting object to string type, making it loggable
        for key, value in kwargs.items():
            if not self._is_valid_json_type(value):
                kwargs[key] = str(value)

        json_order.update(kwargs)

        try:
            json_output = json.dumps(json_order)
        except TypeError as e:
            json_output = json.dumps(
                OrderedDict(
                    [
                        ("time", asctime),
                        ("level", "ERROR"),
                        ("msg", f"Failed to serialize log message: {e}"),
                    ]
                ),
            )

        if self.sd_log is True:
            log_to_sd(asctime, json_output)

        if self._can_print_this_level(level_value):
            if self.colorized:
                json_output = json_output.replace(
                    f'"level": "{level}"', f'"level": "{LogColors[level]}"'
                )
            print(json_output)

    def debug(self, message: str, **kwargs) -> None:
        """
        Log a message with severity level DEBUG.
        """
        self._log("DEBUG", 1, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """
        Log a message with severity level INFO.
        """
        self._log("INFO", 2, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """
        Log a message with severity level WARNING.
        """
        self._log("WARNING", 3, message, **kwargs)

    def error(self, message: str, err: Exception, **kwargs) -> None:
        """
        Log a message with severity level ERROR.
        """
        kwargs["err"] = traceback.format_exception(err)
        self._error_counter.increment()
        self._log("ERROR", 4, message, **kwargs)

    def critical(self, message: str, err: Exception, **kwargs) -> None:
        """
        Log a message with severity level CRITICAL.
        """
        kwargs["err"] = traceback.format_exception(err)
        self._error_counter.increment()
        self._log("CRITICAL", 5, message, **kwargs)

    def get_error_count(self) -> int:
        return self._error_counter.get()
