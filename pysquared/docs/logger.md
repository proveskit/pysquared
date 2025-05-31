# Logger

### logger Module
This module provides the `Logger` class for handling logging messages with different severity levels. Logs can be output to standard output or saved to a file (functionality to be implemented). Includes colorized output and error counting.

#### Imports
```py title="logger.py"
import json
import time
import traceback
from collections import OrderedDict

from .nvm.counter import Counter
```

### Color Utility

#### Function: `_color`
Returns a colorized string for terminal output.

##### Arguments
- **msg** (str): The message to colorize.
- **color** (str): The color name.
- **fmt** (str): The formatting style.

##### Returns
- **str**: The colorized message.

```py title="logger.py"
def _color(msg, color="gray", fmt="normal") -> str:
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
```

### LogColors Dictionary
Maps log level names to colorized strings for terminal output.

```py title="logger.py"
LogColors = {
    "NOTSET": "NOTSET",
    "DEBUG": _color(msg="DEBUG", color="blue"),
    "INFO": _color(msg="INFO", color="green"),
    "WARNING": _color(msg="WARNING", color="orange"),
    "ERROR": _color(msg="ERROR", color="pink"),
    "CRITICAL": _color(msg="CRITICAL", color="red"),
}
```

### LogLevel Class
Defines log level constants for Logger.

#### Attributes
- **NOTSET** (int): 0
- **DEBUG** (int): 1
- **INFO** (int): 2
- **WARNING** (int): 3
- **ERROR** (int): 4
- **CRITICAL** (int): 5

```py title="logger.py"
class LogLevel:
    NOTSET = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
```

### Logger Class
Handles logging messages with different severity levels, colorized output, and error counting.

#### Attributes
- **_error_counter** (Counter): Counter for error occurrences.
- **_log_level** (int): Current log level.
- **colorized** (bool): Whether to colorize output.

### Initialization of Logger Instance

#### Arguments
- **error_counter** (Counter): Counter for error occurrences.
- **log_level** (int): Initial log level.
- **colorized** (bool): Whether to colorize output.

```py title="logger.py"
def __init__(
    self,
    error_counter: Counter,
    log_level: int = LogLevel.NOTSET,
    colorized: bool = False,
) -> None:
    self._error_counter: Counter = error_counter
    self._log_level: int = log_level
    self.colorized: bool = colorized
```

### Logging Methods

#### Function: `debug`
Logs a message with severity level DEBUG.

##### Arguments
- **message** (str): The log message.
- **kwargs**: Additional key/value pairs to include in the log.

```py title="logger.py"
def debug(self, message: str, **kwargs) -> None:
    self._log("DEBUG", 1, message, **kwargs)
```

#### Function: `info`
Logs a message with severity level INFO.

##### Arguments
- **message** (str): The log message.
- **kwargs**: Additional key/value pairs to include in the log.

```py title="logger.py"
def info(self, message: str, **kwargs) -> None:
    self._log("INFO", 2, message, **kwargs)
```

#### Function: `warning`
Logs a message with severity level WARNING.

##### Arguments
- **message** (str): The log message.
- **kwargs**: Additional key/value pairs to include in the log.

```py title="logger.py"
def warning(self, message: str, **kwargs) -> None:
    self._log("WARNING", 3, message, **kwargs)
```

#### Function: `error`
Logs a message with severity level ERROR and increments the error counter.

##### Arguments
- **message** (str): The log message.
- **err** (Exception): The exception to log.
- **kwargs**: Additional key/value pairs to include in the log.

```py title="logger.py"
def error(self, message: str, err: Exception, **kwargs) -> None:
    kwargs["err"] = traceback.format_exception(err)
    self._error_counter.increment()
    self._log("ERROR", 4, message, **kwargs)
```

#### Function: `critical`
Logs a message with severity level CRITICAL and increments the error counter.

##### Arguments
- **message** (str): The log message.
- **err** (Exception): The exception to log.
- **kwargs**: Additional key/value pairs to include in the log.

```py title="logger.py"
def critical(self, message: str, err: Exception, **kwargs) -> None:
    kwargs["err"] = traceback.format_exception(err)
    self._error_counter.increment()
    self._log("CRITICAL", 5, message, **kwargs)
```

#### Function: `get_error_count`
Returns the current error count.

##### Returns
- **int**: The number of errors logged.

```py title="logger.py"
def get_error_count(self) -> int:
    return self._error_counter.get()
```