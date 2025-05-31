# Digital IO Initialization

### digitalio Module
This module provides functions for initializing DigitalInOut pins on the PySquared satellite hardware. It includes retry logic for robust hardware initialization and error handling.

#### Imports
```py title="digitalio.py"
from digitalio import DigitalInOut, Direction
from microcontroller import Pin

from ..logger import Logger
from .decorators import with_retries
from .exception import HardwareInitializationError
```

### Digital Pin Initialization

#### Function: `initialize_pin`
Initializes a DigitalInOut pin with the specified direction and initial value. Includes retry logic for robust hardware setup.

##### Arguments
- **logger** (Logger): The logger instance to log messages.
- **pin** (Pin): The pin to initialize.
- **direction** (Direction): The direction of the pin.
- **initial_value** (bool): The initial value of the pin (default is True).

##### Returns
- **DigitalInOut**: The initialized DigitalInOut object.

##### Raises
- **HardwareInitializationError**: If the pin fails to initialize.

```py title="digitalio.py"
@with_retries(max_attempts=3, initial_delay=1)
def initialize_pin(
    logger: Logger, pin: Pin, direction: Direction, initial_value: bool
) -> DigitalInOut:
    logger.debug(message="Initializing pin", initial_value=initial_value, pin=pin)

    try:
        digital_in_out = DigitalInOut(pin)
        digital_in_out.direction = direction
        digital_in_out.value = initial_value
        return digital_in_out
    except Exception as e:
        raise HardwareInitializationError("Failed to initialize pin") from e
```
