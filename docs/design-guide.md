# Design Guide

This document provides an overview of the design principles and architecture of the PySquared Flight Software. It is intended for developers who want to understand how the software is structured and how to contribute effectively.

## CircuitPython

PySquared is built on top of CircuitPython, which is a version of Python designed for microcontrollers. CircuitPython is a fork of MicroPython which adhears to a subset of the Python language specification. Python 3.4 syntax is supported with some additional features pulled from later releases such as type hinting.

### Resources

- [Python 3.4 Reference](https://docs.python.org/3.4/reference/index.html)
- [Differences between MicroPython and Python](https://docs.micropython.org/en/latest/genrst/index.html#cpython-diffs)
- [Differences between CircuitPython and MicroPython](https://docs.circuitpython.org/en/latest/README.html#differences-from-micropython)
- [CircuitPython Shared Bindings Documentation](https://docs.circuitpython.org/en/latest/shared-bindings/index.html)
- [CircuitPython Standard Libraries Documentation](https://docs.circuitpython.org/en/latest/docs/library/index.html)
- [CircuitPython Design Guide](https://docs.circuitpython.org/en/latest/docs/design_guide.html)

## Types and Type Checking

We use type hints throughout the PySquared codebase to ensure that our code is clear and maintainable. Type hints help us catch errors early and make it easier to understand the expected types of variables and function parameters.

We do not accept changes with lines that are ignored the type checker i.e. `# type: ignore`. If you run into an issue where you think you need to ignore a type, it is likely a problem with the design of your component. Please take a moment to think about how you can fix the type error instead. If you need help, please reach out for assistance.

??? note "Using the Typing Module"
    For more advanced type hinting we can use the Python standard library's `typing` module which was introduced in Python 3.5. This module provides a variety of type hints that can be used to specify more complex types, such as `List`, `Dict`, and `Optional`. CircuitPython does not support the `typing` module so we must wrap the import in a try/except block to avoid import errors. For example:

    ```python
    try:
        from typing import List, Dict, Optional
    except ImportError:
        pass
    ```

    This pattern allows us to use type hints in our code while still being compatible with CircuitPython.

    Additionally we cannot use `typing`'s `Any` type hint in CircuitPython. Instead, we can use `object` as a generic type hint.

## Protocols

Protocols are a way to define a set of methods that a class must implement. They are similar to interfaces in other programming languages or header files in C. Protocols allow us to define a contract for classes to follow, ensuring that they implement the required methods. CircuitPython does not support Protocols, so we use base classes to define our protocols where all required methods are implemented with `...` (Ellipsis). All classes that implement the protocol must override these methods. Protocols can be found in `pysquared/protos/`.

## Testing

We use [pytest](https://docs.pytest.org/en/stable/) for unit testing our code. We are designing software for spacecraft, so it is important that we have a robust testing framework to ensure our code is reliable and works as expected. We write tests for all of our code, and we run these tests automatically using GitHub Actions. We aim to have 100% test coverage for all of our code, which means that every line of code is tested by at least one test case.

## Documentation

We use [MkDocs](https://www.mkdocs.org/) to build our documentation. We write our documentation in Markdown, which is a lightweight markup language that is easy to read and write. We document our code using docstrings, which are special comments that describe the purpose and usage of a function or class. We also use type hints in our docstrings to provide additional information about the expected types of parameters and return values. Where it makes sense, add usage examples following [CommonMark fenced code blocks](https://spec.commonmark.org/0.30/#fenced-code-blocks) to document how to use your code.

### Module Documentation

Start with a brief summary, followed by an optional extended description:

```python
"""This module provides utilities for parsing and validating telemetry data from spacecraft sensors.

It includes classes and functions for decoding sensor packets, verifying data integrity, and converting
raw readings into SI units for further analysis.
"""
```

### Class Documentation

Begin with a short description, a detailed explanation, and a practical usage example:

```python
"""The TelemetryParser class extracts and validates sensor readings from raw telemetry packets.

TelemetryParser handles packet decoding, error checking, and conversion to SI units. It is designed
for use in spacecraft flight software where reliable sensor data is critical.

**Usage:**
~~~python
from pysquared.telemetry import TelemetryParser

parser = TelemetryParser()
packet = b'\x01\x02\x03\x04'
reading = parser.parse(packet)
print(reading.timestamp, reading.acceleration)  # Output: 2024-06-01T12:00:00Z (0.0, 9.8, 0.0)
~~~
"""
```

### Function/Method Documentation

Include a description, argument details, return values, and any exceptions raised:

```python
"""
Validate a sensor reading and convert it to SI units.

Args:
    reading: Raw sensor reading with keys 'value' and 'unit'.
    sensor_type: Type of sensor (e.g., 'acceleration', 'temperature').

Returns:
    float: The validated reading in SI units.

Raises:
    KeyError: If required keys are missing from the reading.
    ValueError: If the reading value is out of expected range.
"""
```

## Sensor Readings

All sensor readings must be in SI units and stored in a structure that includes the time of the reading. Including the time of the reading is important for analysing sensor data and ensuring that processes such as detumbling and attitude control can be performed accurately.

The following table lists possible sensor properties, their corresponding types and units for common sensor readings. The table was pulled directly from the [CircuitPython Design Guide](https://docs.circuitpython.org/en/latest/docs/design_guide.html#sensor-properties-and-units):

| Property Name    | Python Type          | Units / Description                          |
|------------------|----------------------|----------------------------------------------|
| acceleration     | (float, float, float)| x, y, z meter per second²                    |
| alarm            | (time.struct, str)   | Sample alarm time and frequency string       |
| CO2              | float                | measured CO₂ in ppm                          |
| color            | int                  | RGB, eight bits per channel (0xff0000 is red)|
| current          | float                | milliamps (mA)                               |
| datetime         | time.struct          | date and time                                |
| distance         | float                | centimeters (cm)                             |
| duty_cycle       | int                  | 16-bit PWM duty cycle                        |
| eCO2             | float                | equivalent/estimated CO₂ in ppm              |
| frequency        | int                  | Hertz (Hz)                                   |
| angular velocity | (float, float, float)| x, y, z radians per second                   |
| light            | float                | non-unit-specific light levels               |
| lux              | float                | SI lux                                       |
| magnetic         | (float, float, float)| x, y, z micro-Tesla (uT)                     |
| orientation      | (float, float, float)| x, y, z degrees                              |
| pressure         | float                | hectopascal (hPa)                            |
| proximity        | int                  | non-unit-specific proximity values           |
| relative_humidity| float                | percent                                      |
| sound_level      | float                | non-unit-specific sound level                |
| temperature      | float                | degrees Celsius                              |
| TVOC             | float                | Total Volatile Organic Compounds in ppb      |
| voltage          | float                | volts (V)                                    |
| weight           | float                | grams (g)                                    |

Definitions for sensor readings can be found in `pysquared/sensors/`

!!! warning "Handling Sensor Reading Failures"
    Sensor reading failures must be expected and handled gracefully. If a sensor reading fails, the code should log an error message and return a default value (e.g., `0.0` for numeric readings or `None` for optional readings). This ensures that the system can continue to operate even if a sensor is temporarily unavailable. In the case of a sensor hanging, the attempt must time out and return a default value.

### Resources
- [Adafruit Unified Sensor Driver](https://learn.adafruit.com/using-the-adafruit-unified-sensor-driver?view=all)
- [Android Motion Sensor Documentation](https://developer.android.com/develop/sensors-and-location/sensors/sensors_motion)
- [Android Position Sensor Documentation](https://developer.android.com/develop/sensors-and-location/sensors/sensors_position)
- [Android Environment Sensor Documentation](https://developer.android.com/develop/sensors-and-location/sensors/sensors_environment)

## Dependency Management
We use [`uv`](https://docs.astral.sh/uv/) for managing our python development environment and dependencies. It allows us to define our dependencies in a `pyproject.toml` file and provides a consistent way to install and manage them across different environments. We use dependency groups to separate the dependencies needed for running on the satellite `pyproject.dependencies`, development `pyproject.dev`, and documentation `pyproject.docs`.

`uv` is downloaded and installed automatically when you use run `make` commands. Please see the [Makefile](Makefile) or `make help` for more information on how to use `uv` to manage your development environment.

## Linting and Code Style
We use [`ruff`](https://docs.astral.sh/ruff/) for linting and formatting our code. `ruff` is a fast, extensible linter that checks our code for errors and enforces specific coding standards and style. We use `ruff`'s [default configuration](https://github.com/astral-sh/ruff/tree/0.12.3?tab=readme-ov-file#configuration) with only one addition, isort (`-I`), for linting and formatting our code.

### Linting
`ruff` checks our code for errors following [pyflakes](https://pypi.org/project/pyflakes/) logic.

### Code Style
By default `ruff`, enforces the [`black`](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html) style with [a few deviations](https://docs.astral.sh/ruff/formatter/#style-guide) decided by `ruff` for formatting our code. Code formatting ensures that our code is consistent and easy to read.

## Error Handling

Error handling in PySquared is designed to be robust and predictable. We use standard `try...except` blocks to catch exceptions. When an exception is caught, it should be logged with the `logger.error()` or `logger.critical()` method. This ensures that we have a record of the error and can diagnose it later.

```python
try:
    # Code that may raise an exception
except Exception as e:
    logger.error("An error occurred", err=e)
```

Custom exceptions should be used to represent specific error conditions in your code. This allows us to handle different types of errors in a more granular way. Custom exceptions should inherit from the built-in `Exception` class and should be named using the `Error` suffix.

```python
class CustomError(Exception):
    """Custom exception for specific error conditions."""
    pass

try:
    # Code that may raise a CustomError
except CustomError as e:
    logger.error("A custom error occurred", err=e)
```

When raising exceptions, always provide a clear and descriptive error message. This will help us understand the context of the error when it is logged.

```python
raise CustomError("This is a custom error message")
```

## Logging

The syntax for our logging module `logger` is based off the popular Python logger [`Loguru`](https://loguru.readthedocs.io/en/stable/). We use the `logger` module to log messages at different levels (`debug`, `info`, `warning`, `error`, `critical`) throughout our code. This allows us to track the flow of execution and diagnose issues when they arise.

Logs are structured as JSON, which makes them easy to parse and analyze. When logging, you can include additional key-value pairs to provide context.

```python
logger.info("User logged in", user_id=123)
```

Code that raises an exception should log at the `error` level. Code that failed but is recoverable should log at the `warning` level. The `debug` level should be used to understand the flow of the program during development and debugging. The `info` level should be used for general information about the program's execution, such as startup, shutdown, and other important updates. `critical` should be used for serious errors that may prevent the satellite from continuing operation, requiring a restart.

## Configuration

Configuration management in PySquared is centralized in the `Config` class. This class is responsible for loading, validating, and providing access to all configuration settings, which are stored in a JSON file.

### Loading and Accessing Configuration

The `Config` class is initialized with the path to the configuration file. It parses the JSON and exposes the settings as attributes.

**Usage:**
```python
from pysquared.config import Config

# Initialize the config with the path to your settings file
config = Config("config.json")

# Access configuration values directly
print(f"Satellite Name: {config.cubesat_name}")
print(f"Sleep Duration: {config.sleep_duration} seconds")
```

### Updating Configuration

The `update_config` method allows for both temporary (in-memory) and permanent (persisted to the JSON file) changes to the configuration.

- **Temporary Updates:** Changes are only applied to the `Config` object in memory and will be lost on restart.
- **Permanent Updates:** Changes are written back to the configuration file.

```python
# Temporarily update the sleep duration
config.update_config("sleep_duration", 120, temporary=True)

# Permanently update the satellite's name
config.update_config("cubesat_name", "PyCubed", temporary=False)
```

### Validation

The `Config` class includes a validation schema to ensure that all configuration values are within expected ranges and of the correct type. Any attempt to set an invalid value will raise a `TypeError` or `ValueError`. This helps prevent runtime errors due to misconfiguration.

### Radio Configuration

Radio-specific settings are managed by the `RadioConfig` class, which is a nested object within the main `Config` class.

## Imports
We use relative imports for all of our modules. This allows us to easily import pysquared into downstream libraries like our board specific repos. For example, if we have a module `pysquared.sensors.temperature`, we can import it in another module using:

```python
from .sensors.temperature import TemperatureSensor
```

## Non-Volatile Memory (NVM)
We use the `pysquared.nvm` module to manage non-volatile memory (NVM) on the flight control board. This module provides a way to store persistent data across reboots, such as error counters and other important state information. The NVM module includes a `Counter` class for counting events and a `Flag` class for storing boolean flags.
