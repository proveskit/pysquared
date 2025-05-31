# Hardware Bus Initialization

### busio Module
This module provides functions for initializing and configuring SPI and I2C buses on the PySquared satellite hardware. It includes retry logic for robust hardware initialization and error handling.

#### Imports
```py title="busio.py"
import time

from busio import I2C, SPI
from microcontroller import Pin

from ..logger import Logger
from .decorators import with_retries
from .exception import HardwareInitializationError

try:
    from typing import Optional
except ImportError:
    pass
```

### SPI Bus Initialization

#### Function: `initialize_spi_bus`
Initializes and configures an SPI bus with the specified parameters.

##### Arguments
- **logger** (Logger): Logger instance to log messages.
- **clock** (Pin): The pin to use for the clock signal.
- **mosi** (Optional[Pin]): The pin to use for the MOSI signal.
- **miso** (Optional[Pin]): The pin to use for the MISO signal.
- **baudrate** (Optional[int]): The baudrate of the SPI bus (default 100000).
- **phase** (Optional[int]): The phase of the SPI bus (default 0).
- **polarity** (Optional[int]): The polarity of the SPI bus (default 0).
- **bits** (Optional[int]): The number of bits per transfer (default 8).

##### Returns
- **SPI**: The initialized and configured SPI object.

##### Raises
- **HardwareInitializationError**: If the SPI bus fails to initialize or configure.

```py title="busio.py"
def initialize_spi_bus(
    logger: Logger,
    clock: Pin,
    mosi: Optional[Pin] = None,
    miso: Optional[Pin] = None,
    baudrate: Optional[int] = 100000,
    phase: Optional[int] = 0,
    polarity: Optional[int] = 0,
    bits: Optional[int] = 8,
) -> SPI:
    ...
```

#### Function: `_spi_init`
Initializes an SPI bus (without configuration). Includes retry logic.

##### Arguments
- **logger** (Logger): Logger instance.
- **clock** (Pin): Clock pin.
- **mosi** (Optional[Pin]): MOSI pin.
- **miso** (Optional[Pin]): MISO pin.

##### Returns
- **SPI**: The initialized SPI object.

##### Raises
- **HardwareInitializationError**: If the SPI bus fails to initialize.

```py title="busio.py"
@with_retries(max_attempts=3, initial_delay=1)
def _spi_init(
    logger: Logger,
    clock: Pin,
    mosi: Optional[Pin] = None,
    miso: Optional[Pin] = None,
) -> SPI:
    ...
```

#### Function: `_spi_configure`
Configures an SPI bus with the specified parameters.

##### Arguments
- **logger** (Logger): Logger instance.
- **spi** (SPI): SPI bus to configure.
- **baudrate** (Optional[int]): Baudrate.
- **phase** (Optional[int]): Phase.
- **polarity** (Optional[int]): Polarity.
- **bits** (Optional[int]): Bits per transfer.

##### Returns
- **SPI**: The configured SPI object.

##### Raises
- **HardwareInitializationError**: If the SPI bus cannot be configured.

```py title="busio.py"
def _spi_configure(
    logger: Logger,
    spi: SPI,
    baudrate: Optional[int],
    phase: Optional[int],
    polarity: Optional[int],
    bits: Optional[int],
) -> SPI:
    ...
```

### I2C Bus Initialization

#### Function: `initialize_i2c_bus`
Initializes an I2C bus with the specified parameters. Includes retry logic.

##### Arguments
- **logger** (Logger): Logger instance to log messages.
- **scl** (Pin): The pin to use for the SCL signal.
- **sda** (Pin): The pin to use for the SDA signal.
- **frequency** (Optional[int]): The baudrate of the I2C bus (default 100000).

##### Returns
- **I2C**: The initialized I2C object.

##### Raises
- **HardwareInitializationError**: If the I2C bus fails to initialize.

```py title="busio.py"
@with_retries(max_attempts=3, initial_delay=1)
def initialize_i2c_bus(
    logger: Logger,
    scl: Pin,
    sda: Pin,
    frequency: Optional[int],
) -> I2C:
    ...
```