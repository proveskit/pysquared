# pysquared

PySquared Satellite Flight Software

Modules:

- **`beacon`** – This module provides a Beacon class for sending periodic status messages.
- **`cdh`** – This module provides the CommandDataHandler for managing and processing commands.
- **`config`** – This module provides an interface for managing configuration settings in the PySquared project.
- **`detumble`** – This module provides functions for satellite detumbling using magnetorquers.
- **`hardware`** – This module provides managers for various hardware components including sensors, actuators, communication interfaces, etc.
- **`logger`** – This module provides a Logger class for handling logging messages.
- **`nvm`** – The NVM package is a collection of functionality that interacts with non-volatile memory
- **`power_health`** – This module provides a PowerHealth class for monitoring the power system.
- **`protos`** – This module defines hardware agnostic protocols for accessing devices with certain features.
- **`rtc`** – This module provides Real-Time Clock (RTC) management functionality for the PySquared satellite.
- **`sleep_helper`** – This module provides the SleepHelper class for managing safe sleep and hibernation
- **`watchdog`** – This module provides the Watchdog class for managing the hardware watchdog timer

## beacon

This module provides a Beacon class for sending periodic status messages.

The Beacon class collects data from various sensors and system components, formats it as a JSON string, and sends it using a provided packet manager. This is typically used for sending telemetry or health information from a satellite or remote device.

**Usage:**

```python
logger = Logger()
packet_manager = PacketManager(logger, radio)
boot_time = time.time()
beacon = Beacon(logger, "MySat", packet_manager, boot_time, imu, power_monitor)
beacon.send()

```

Classes:

- **`Beacon`** – A beacon for sending status messages.

### Beacon

```python
Beacon(logger: Logger, name: str, packet_manager: PacketManager, boot_time: float, *args: PowerMonitorProto | RadioProto | IMUProto | TemperatureSensorProto | Flag | Counter | Processor)

```

A beacon for sending status messages.

Parameters:

- #### **`logger`**

  (`Logger`) – The logger to use.

- #### **`name`**

  (`str`) – The name of the beacon.

- #### **`packet_manager`**

  (`PacketManager`) – The packet manager to use for sending the beacon.

- #### **`boot_time`**

  (`float`) – The time the system booted.

- #### **`*args`**

  (`PowerMonitorProto | RadioProto | IMUProto | TemperatureSensorProto | Flag | Counter | Processor`, default: `()` ) – A list of sensors and other components to include in the beacon.

Methods:

- **`avg_readings`** – Gets the average of the readings from a function.
- **`send`** – Sends the beacon.

#### avg_readings

```python
avg_readings(func: Callable[..., float | None], num_readings: int = 50) -> float | None

```

Gets the average of the readings from a function.

Parameters:

- ##### **`func`**

  (`Callable[..., float | None]`) – The function to call.

- ##### **`num_readings`**

  (`int`, default: `50` ) – The number of readings to take.

Returns:

- `float | None` – The average of the readings, or None if the readings could not be taken.

#### send

```python
send() -> bool

```

Sends the beacon.

Returns:

- `bool` – True if the beacon was sent successfully, False otherwise.

## cdh

This module provides the CommandDataHandler for managing and processing commands.

This module is responsible for handling commands received by the satellite. It includes command parsing, validation, execution, and handling of radio communications. The CommandDataHandler class is the main entry point for this functionality.

**Usage:**

```python
logger = Logger()
config = Config("config.json")
packet_manager = PacketManager(logger, radio)
cdh = CommandDataHandler(logger, config, packet_manager)
cdh.listen_for_commands(timeout=60)

```

Classes:

- **`CommandDataHandler`** – Handles command parsing, validation, and execution for the satellite.

### CommandDataHandler

```python
CommandDataHandler(logger: Logger, config: Config, packet_manager: PacketManager, send_delay: float = 0.2)

```

Handles command parsing, validation, and execution for the satellite.

Parameters:

- #### **`logger`**

  (`Logger`) – The logger to use.

- #### **`config`**

  (`Config`) – The configuration to use.

- #### **`packet_manager`**

  (`PacketManager`) – The packet manager to use for sending and receiving data.

- #### **`send_delay`**

  (`float`, default: `0.2` ) – The delay between sending an acknowledgement and the response.

Methods:

- **`change_radio_modulation`** – Changes the radio modulation.
- **`listen_for_commands`** – Listens for commands from the radio and handles them.
- **`reset`** – Resets the hardware.
- **`send_joke`** – Sends a random joke from the config.

#### change_radio_modulation

```python
change_radio_modulation(args: list[str]) -> None

```

Changes the radio modulation.

Parameters:

- ##### **`args`**

  (`list[str]`) – A list of arguments, the first item must be the new modulation. All other items in the args list are ignored.

#### listen_for_commands

```python
listen_for_commands(timeout: int) -> None

```

Listens for commands from the radio and handles them.

Parameters:

- ##### **`timeout`**

  (`int`) – The time in seconds to listen for commands.

#### reset

```python
reset() -> None

```

Resets the hardware.

#### send_joke

```python
send_joke() -> None

```

Sends a random joke from the config.

## config

This module provides an interface for managing configuration settings in the PySquared project.

Modules:

- **`config`** – This module provides the Config, which encapsulates the configuration
- **`radio`** – This module provides classes for handling and validating radio configuration parameters, including support for both FSK and LoRa modulation schemes.

### config

This module provides the Config, which encapsulates the configuration logic for the PySquared project. It loads, validates, and updates configuration values from a JSON file, and distributes these values across the application.

Classes:

- **`Config`** – Handles loading, validating, and updating configuration values, including radio settings.

**Usage:**

```python
config = Config("config.json")
config.update_config("cubesat_name", "Cube1", temporary=False)

```

#### Config

```python
Config(config_path: str)

```

Configuration handler for PySquared.

Loads configuration from a JSON file, validates values, and provides methods to update configuration settings. Supports both temporary (RAM-only) and permanent (file-persisted) updates. Delegates radio-related validation and updates to the RadioConfig class.

Attributes:

- **`config_file`** (`str`) – Path to the configuration JSON file.
- **`radio`** (`RadioConfig`) – Radio configuration handler.
- **`cubesat_name`** (`str`) – Name of the cubesat.
- **`sleep_duration`** (`int`) – Sleep duration in seconds.
- **`detumble_enable_z`** (`bool`) – Enable detumbling on Z axis.
- **`detumble_enable_x`** (`bool`) – Enable detumbling on X axis.
- **`detumble_enable_y`** (`bool`) – Enable detumbling on Y axis.
- **`jokes`** (`list[str]`) – List of jokes for the cubesat.
- **`debug`** (`bool`) – Debug mode flag.
- **`heating`** (`bool`) – Heating system enabled flag.
- **`normal_temp`** (`int`) – Normal operating temperature.
- **`normal_battery_temp`** (`int`) – Normal battery temperature.
- **`normal_micro_temp`** (`int`) – Normal microcontroller temperature.
- **`normal_charge_current`** (`float`) – Normal charge current.
- **`normal_battery_voltage`** (`float`) – Normal battery voltage.
- **`critical_battery_voltage`** (`float`) – Critical battery voltage.
- **`reboot_time`** (`int`) – Time before reboot in seconds.
- **`turbo_clock`** (`bool`) – Turbo clock enabled flag.
- **`super_secret_code`** (`str`) – Secret code for special operations.
- **`repeat_code`** (`str`) – Code for repeated operations.
- **`longest_allowable_sleep_time`** (`int`) – Maximum allowable sleep time.
- **`CONFIG_SCHEMA`** (`dict`) – Validation schema for configuration keys.

Methods:

- **`validate`** – Validates a configuration value against its schema.
- **`_save_config`** – Saves a configuration value to the JSON file.
- **`update_config`** – Updates a configuration value, either temporarily or permanently.

Parameters:

- ##### **`config_path`**

  (`str`) – Path to the configuration JSON file.

Raises:

- `FileNotFoundError` – If the configuration file does not exist.
- `JSONDecodeError` – If the configuration file is not valid JSON.

##### update_config

```python
update_config(key: str, value, temporary: bool) -> None

```

Updates a configuration value, either temporarily (RAM only) or permanently (persisted to file).

Parameters:

- ###### **`key`**

  (`str`) – The configuration key to update.

- ###### **`value`**

  – The new value to set.

- ###### **`temporary`**

  (`bool`) – If True, update only in RAM; if False, persist to file.

Raises:

- `TypeError` – If the value is not of the expected type.
- `ValueError` – If the value is out of the allowed range or length.

##### validate

```python
validate(key: str, value) -> None

```

Validates a configuration value against its schema.

Parameters:

- ###### **`key`**

  (`str`) – The configuration key to validate.

- ###### **`value`**

  – The value to validate.

Raises:

- `TypeError` – If the value is not of the expected type.
- `ValueError` – If the value is out of the allowed range or length.

### radio

This module provides classes for handling and validating radio configuration parameters, including support for both FSK and LoRa modulation schemes.

Classes:

- **`RadioConfig`** – Handles top-level radio configuration and validation.
- **`FSKConfig`** – Handles FSK-specific configuration and validation.
- **`LORAConfig`** – Handles LoRa-specific configuration and validation.

#### FSKConfig

```python
FSKConfig(fsk_dict: dict)

```

Handles FSK-specific radio configuration and validation.

Attributes:

- **`broadcast_address`** (`int`) – Broadcast address for FSK.
- **`node_address`** (`int`) – Node address for FSK.
- **`modulation_type`** (`int`) – Modulation type for FSK.
- **`FSK_SCHEMA`** (`dict`) – Validation schema for FSK configuration keys.

Parameters:

- ##### **`fsk_dict`**

  (`dict`) – Dictionary containing FSK configuration values.

#### LORAConfig

```python
LORAConfig(lora_dict: dict)

```

Handles LoRa-specific radio configuration and validation.

Attributes:

- **`ack_delay`** (`float`) – Acknowledgement delay in seconds.
- **`coding_rate`** (`int`) – Coding rate for LoRa.
- **`cyclic_redundancy_check`** (`bool`) – CRC enabled flag.
- **`spreading_factor`** (`Literal[6, 7, 8, 9, 10, 11, 12]`) – LoRa spreading factor.
- **`transmit_power`** (`int`) – Transmit power in dBm.
- **`LORA_SCHEMA`** (`dict`) – Validation schema for LoRa configuration keys.

Parameters:

- ##### **`lora_dict`**

  (`dict`) – Dictionary containing LoRa configuration values.

#### RadioConfig

```python
RadioConfig(radio_dict: dict)

```

Handles radio configuration and validation for PySquared.

Attributes:

- **`license`** (`str`) – The radio license identifier.
- **`modulation`** (`Literal['LoRa', 'FSK']`) – The modulation type.
- **`transmit_frequency`** (`int`) – The transmission frequency in MHz.
- **`start_time`** (`int`) – The radio start time in seconds.
- **`fsk`** (`FSKConfig`) – FSK-specific configuration handler.
- **`lora`** (`LORAConfig`) – LoRa-specific configuration handler.
- **`RADIO_SCHEMA`** (`dict`) – Validation schema for radio configuration keys.

Methods:

- **`validate`** – Validates a radio configuration value against its schema.

Parameters:

- ##### **`radio_dict`**

  (`dict`) – Dictionary containing radio configuration values.

##### validate

```python
validate(key: str, value) -> None

```

Validates a radio configuration value against its schema.

Parameters:

- ###### **`key`**

  (`str`) – The configuration key to validate.

- ###### **`value`**

  – The value to validate.

Raises:

- `KeyError` – If the key is not found in any schema.
- `TypeError` – If the value is not of the expected type or not allowed.
- `ValueError` – If the value is out of the allowed range.

## detumble

This module provides functions for satellite detumbling using magnetorquers. Includes vector math utilities and the main dipole calculation for attitude control.

Functions:

- **`dot_product`** – Computes the dot product of two 3-element vectors.
- **`gain_func`** – Returns the gain value for the detumble control law.
- **`magnetorquer_dipole`** – Calculates the required dipole moment for the magnetorquers to detumble the satellite.
- **`x_product`** – Computes the cross product of two 3-element vectors.

### dot_product

```python
dot_product(vector1: tuple, vector2: tuple) -> float

```

Computes the dot product of two 3-element vectors.

Parameters:

- #### **`vector1`**

  (`tuple`) – First vector (length 3).

- #### **`vector2`**

  (`tuple`) – Second vector (length 3).

Returns:

- **`float`** ( `float` ) – The dot product of the two vectors.

### gain_func

```python
gain_func() -> float

```

Returns the gain value for the detumble control law.

Returns:

- **`float`** ( `float` ) – Gain value (default 1.0).

### magnetorquer_dipole

```python
magnetorquer_dipole(mag_field: tuple, ang_vel: tuple) -> list

```

Calculates the required dipole moment for the magnetorquers to detumble the satellite.

Parameters:

- #### **`mag_field`**

  (`tuple`) – The measured magnetic field vector (length 3).

- #### **`ang_vel`**

  (`tuple`) – The measured angular velocity vector (length 3).

Returns:

- **`list`** ( `list` ) – The dipole moment vector to be applied (length 3).

### x_product

```python
x_product(vector1: tuple, vector2: tuple) -> list

```

Computes the cross product of two 3-element vectors.

Parameters:

- #### **`vector1`**

  (`tuple`) – First vector (length 3).

- #### **`vector2`**

  (`tuple`) – Second vector (length 3).

Returns:

- **`list`** ( `list` ) – The cross product vector (length 3).

## hardware

This module provides managers for various hardware components including sensors, actuators, communication interfaces, etc.

Modules:

- **`burnwire`** – This module provides an interface for controlling burnwire systems.
- **`busio`** – This module provides functions for initializing and configuring SPI and I2C buses
- **`digitalio`** – This module provides functions for initializing DigitalInOut pins on the PySquared
- **`exception`** – This module provides a custom exception for hardware initialization errors.
- **`imu`** – This module provides an interface for controlling inertial measurement units (IMUs).
- **`magnetometer`** – This module provides an interface for controlling magnetormeters.
- **`power_monitor`** – This module provides an interface for controlling power monitors.
- **`radio`** – This module provides an interface for controlling radios.

### burnwire

This module provides an interface for controlling burnwire systems.

Modules:

- **`manager`** – This module provides the managers for various burnwire implementations

#### manager

This module provides the managers for various burnwire implementations

Modules:

- **`burnwire`** – This module defines the BurnwireManager class, which provides a high-level interface

##### burnwire

This module defines the `BurnwireManager` class, which provides a high-level interface for controlling burnwire circuits, which are commonly used for deployment mechanisms in satellites. It handles the timing and sequencing of the burnwire activation and provides error handling and logging.

**Usage:**

```python
logger = Logger()
enable_pin = DigitalInOut(board.D1)
fire_pin = DigitalInOut(board.D2)
burnwire = BurnwireManager(logger, enable_pin, fire_pin)
burnwire.burn()

```

Classes:

- **`BurnwireManager`** – Manages the activation of a burnwire.

###### BurnwireManager

```python
BurnwireManager(logger: Logger, enable_burn: DigitalInOut, fire_burn: DigitalInOut, enable_logic: bool = True)

```

Bases: `BurnwireProto`

Manages the activation of a burnwire.

Parameters:

- ###### **`logger`**

  (`Logger`) – The logger to use.

- ###### **`enable_burn`**

  (`DigitalInOut`) – The pin used to enable the burnwire circuit.

- ###### **`fire_burn`**

  (`DigitalInOut`) – The pin used to fire the burnwire.

- ###### **`enable_logic`**

  (`bool`, default: `True` ) – The logic level to enable the burnwire.

Methods:

- **`burn`** – Fires the burnwire for a specified amount of time.

###### burn

```python
burn(timeout_duration: float = 5.0) -> bool

```

Fires the burnwire for a specified amount of time.

Parameters:

- ###### **`timeout_duration`**

  (`float`, default: `5.0` ) – The maximum amount of time to keep the burnwire on.

Returns:

- `bool` – True if the burn was successful, False otherwise.

Raises:

- `Exception` – If there is an error toggling the burnwire pins.

### busio

This module provides functions for initializing and configuring SPI and I2C buses on the PySquared satellite hardware. Includes retry logic for robust hardware initialization and error handling.

Functions:

- **`initialize_i2c_bus`** – Initializes an I2C bus with the specified parameters. Includes retry logic.
- **`initialize_spi_bus`** – Initializes and configures an SPI bus with the specified parameters.

#### initialize_i2c_bus

```python
initialize_i2c_bus(logger: Logger, scl: Pin, sda: Pin, frequency: Optional[int]) -> I2C

```

Initializes an I2C bus with the specified parameters. Includes retry logic.

Parameters:

- ##### **`logger`**

  (`Logger`) – Logger instance to log messages.

- ##### **`scl`**

  (`Pin`) – The pin to use for the SCL signal.

- ##### **`sda`**

  (`Pin`) – The pin to use for the SDA signal.

- ##### **`frequency`**

  (`Optional[int]`) – The baudrate of the I2C bus (default 100000).

Raises:

- `HardwareInitializationError` – If the I2C bus fails to initialize.

Returns:

- **`I2C`** ( `I2C` ) – The initialized I2C object.

#### initialize_spi_bus

```python
initialize_spi_bus(logger: Logger, clock: Pin, mosi: Optional[Pin] = None, miso: Optional[Pin] = None, baudrate: Optional[int] = 100000, phase: Optional[int] = 0, polarity: Optional[int] = 0, bits: Optional[int] = 8) -> SPI

```

Initializes and configures an SPI bus with the specified parameters.

Parameters:

- ##### **`logger`**

  (`Logger`) – Logger instance to log messages.

- ##### **`clock`**

  (`Pin`) – The pin to use for the clock signal.

- ##### **`mosi`**

  (`Optional[Pin]`, default: `None` ) – The pin to use for the MOSI signal.

- ##### **`miso`**

  (`Optional[Pin]`, default: `None` ) – The pin to use for the MISO signal.

- ##### **`baudrate`**

  (`Optional[int]`, default: `100000` ) – The baudrate of the SPI bus (default 100000).

- ##### **`phase`**

  (`Optional[int]`, default: `0` ) – The phase of the SPI bus (default 0).

- ##### **`polarity`**

  (`Optional[int]`, default: `0` ) – The polarity of the SPI bus (default 0).

- ##### **`bits`**

  (`Optional[int]`, default: `8` ) – The number of bits per transfer (default 8).

Raises:

- `HardwareInitializationError` – If the SPI bus fails to initialize.

Returns:

- **`SPI`** ( `SPI` ) – The initialized SPI object.

### digitalio

This module provides functions for initializing DigitalInOut pins on the PySquared satellite hardware. Includes retry logic for robust hardware initialization and error handling.

Functions:

- **`initialize_pin`** – Initializes a DigitalInOut pin with the specified direction and initial value.

#### initialize_pin

```python
initialize_pin(logger: Logger, pin: Pin, direction: Direction, initial_value: bool) -> DigitalInOut

```

Initializes a DigitalInOut pin with the specified direction and initial value.

Parameters:

- ##### **`logger`**

  (`Logger`) – The logger instance to log messages.

- ##### **`pin`**

  (`Pin`) – The pin to initialize.

- ##### **`direction`**

  (`Direction`) – The direction of the pin.

- ##### **`initial_value`**

  (`bool`) – The initial value of the pin (default is True).

Raises:

- `HardwareInitializationError` – If the pin fails to initialize.

Returns:

- **`DigitalInOut`** ( `DigitalInOut` ) – The initialized DigitalInOut object.

### exception

This module provides a custom exception for hardware initialization errors.

This exception is raised when a hardware component fails to initialize after a certain number of retries.

**Usage:**

```python
raise HardwareInitializationError("Failed to initialize the IMU.")

```

Classes:

- **`HardwareInitializationError`** – Exception raised for errors in hardware initialization.

#### HardwareInitializationError

Bases: `Exception`

Exception raised for errors in hardware initialization.

### imu

This module provides an interface for controlling inertial measurement units (IMUs).

Modules:

- **`manager`** – This module provides the managers for various inertial measurement unit (IMU) implementations

#### manager

This module provides the managers for various inertial measurement unit (IMU) implementations

Modules:

- **`lsm6dsox`** – This module defines the LSM6DSOXManager class, which provides a high-level interface

##### lsm6dsox

This module defines the `LSM6DSOXManager` class, which provides a high-level interface for interacting with the LSM6DSOX inertial measurement unit. It handles the initialization of the sensor and provides methods for reading gyroscope, acceleration, and temperature data.

**Usage:**

```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
imu = LSM6DSOXManager(logger, i2c, 0x6A)
gyro_data = imu.get_gyro_data()
accel_data = imu.get_acceleration()
temp_data = imu.get_temperature()

```

Classes:

- **`LSM6DSOXManager`** – Manages the LSM6DSOX IMU.

###### LSM6DSOXManager

```python
LSM6DSOXManager(logger: Logger, i2c: I2C, address: int)

```

Bases: `IMUProto`, `TemperatureSensorProto`

Manages the LSM6DSOX IMU.

Parameters:

- ###### **`logger`**

  (`Logger`) – The logger to use.

- ###### **`i2c`**

  (`I2C`) – The I2C bus connected to the chip.

- ###### **`address`**

  (`int`) – The I2C address of the IMU.

Raises:

- `HardwareInitializationError` – If the IMU fails to initialize.

Methods:

- **`get_acceleration`** – Gets the acceleration data from the IMU.
- **`get_gyro_data`** – Gets the gyroscope data from the IMU.
- **`get_temperature`** – Gets the temperature reading from the IMU.

###### get_acceleration

```python
get_acceleration() -> tuple[float, float, float] | None

```

Gets the acceleration data from the IMU.

Returns:

- `tuple[float, float, float] | None` – A tuple containing the x, y, and z acceleration values in m/s^2, or
- `tuple[float, float, float] | None` – None if the data is not available.

###### get_gyro_data

```python
get_gyro_data() -> tuple[float, float, float] | None

```

Gets the gyroscope data from the IMU.

Returns:

- `tuple[float, float, float] | None` – A tuple containing the x, y, and z angular acceleration values in
- `tuple[float, float, float] | None` – radians per second, or None if the data is not available.

###### get_temperature

```python
get_temperature() -> float | None

```

Gets the temperature reading from the IMU.

Returns:

- `float | None` – The temperature in degrees Celsius, or None if the data is not available.

### magnetometer

This module provides an interface for controlling magnetormeters.

Modules:

- **`manager`** – This module provides the managers for various magnetometer implementations

#### manager

This module provides the managers for various magnetometer implementations

Modules:

- **`lis2mdl`** – This module defines the LIS2MDLManager class, which provides a high-level interface

##### lis2mdl

This module defines the `LIS2MDLManager` class, which provides a high-level interface for interacting with the LIS2MDL magnetometer. It handles the initialization of the sensor and provides a method for reading the magnetic field vector.

**Usage:**

```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
magnetometer = LIS2MDLManager(logger, i2c)
mag_data = magnetometer.get_vector()

```

Classes:

- **`LIS2MDLManager`** – Manages the LIS2MDL magnetometer.

###### LIS2MDLManager

```python
LIS2MDLManager(logger: Logger, i2c: I2C)

```

Bases: `MagnetometerProto`

Manages the LIS2MDL magnetometer.

Parameters:

- ###### **`logger`**

  (`Logger`) – The logger to use.

- ###### **`i2c`**

  (`I2C`) – The I2C bus connected to the chip.

Raises:

- `HardwareInitializationError` – If the magnetometer fails to initialize.

Methods:

- **`get_vector`** – Gets the magnetic field vector from the magnetometer.

###### get_vector

```python
get_vector() -> tuple[float, float, float] | None

```

Gets the magnetic field vector from the magnetometer.

Returns:

- `tuple[float, float, float] | None` – A tuple containing the x, y, and z magnetic field values in Gauss, or
- `tuple[float, float, float] | None` – None if the data is not available.

### power_monitor

This module provides an interface for controlling power monitors.

Modules:

- **`manager`** – This module provides the managers for various power monitor implementations

#### manager

This module provides the managers for various power monitor implementations

Modules:

- **`ina219`** – This module defines the INA219Manager class, which provides a high-level interface

##### ina219

This module defines the `INA219Manager` class, which provides a high-level interface for interacting with the INA219 power monitor. It handles the initialization of the sensor and provides methods for reading bus voltage, shunt voltage, and current.

**Usage:**

```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
power_monitor = INA219Manager(logger, i2c, 0x40)
bus_voltage = power_monitor.get_bus_voltage()
shunt_voltage = power_monitor.get_shunt_voltage()
current = power_monitor.get_current()

```

Classes:

- **`INA219Manager`** – Manages the INA219 power monitor.

###### INA219Manager

```python
INA219Manager(logger: Logger, i2c: I2C, addr: int)

```

Bases: `PowerMonitorProto`

Manages the INA219 power monitor.

Parameters:

- ###### **`logger`**

  (`Logger`) – The logger to use.

- ###### **`i2c`**

  (`I2C`) – The I2C bus connected to the chip.

- ###### **`addr`**

  (`int`) – The I2C address of the INA219.

Raises:

- `HardwareInitializationError` – If the INA219 fails to initialize.

Methods:

- **`get_bus_voltage`** – Gets the bus voltage from the INA219.
- **`get_current`** – Gets the current from the INA219.
- **`get_shunt_voltage`** – Gets the shunt voltage from the INA219.

###### get_bus_voltage

```python
get_bus_voltage() -> float | None

```

Gets the bus voltage from the INA219.

Returns:

- `float | None` – The bus voltage in volts, or None if the data is not available.

###### get_current

```python
get_current() -> float | None

```

Gets the current from the INA219.

Returns:

- `float | None` – The current in amps, or None if the data is not available.

###### get_shunt_voltage

```python
get_shunt_voltage() -> float | None

```

Gets the shunt voltage from the INA219.

Returns:

- `float | None` – The shunt voltage in volts, or None if the data is not available.

### radio

This module provides an interface for controlling radios.

Modules:

- **`manager`** – This module provides the managers for various radio implementations.
- **`modulation`** – This module defines the available radio modulation types.
- **`packetizer`** – This package provides an interface for packetizing data for radio communication.

#### manager

This module provides the managers for various radio implementations.

Modules:

- **`base`** – This module provides a base class for radio managers.
- **`rfm9x`** – This module provides a manager for RFM9x radios.
- **`sx126x`** – This module provides a manager for SX126x radios.
- **`sx1280`** – This module provides a manager for SX1280 radios.

##### base

This module provides a base class for radio managers.

This module defines the `BaseRadioManager` class, which serves as an abstract base class for all radio managers in the system. It provides common functionality and ensures that all radio managers adhere to a consistent interface.

Classes:

- **`BaseRadioManager`** – Base class for radio managers (CircuitPython compatible).

###### BaseRadioManager

```python
BaseRadioManager(logger: Logger, radio_config: RadioConfig, **kwargs: object)

```

Bases: `RadioProto`

Base class for radio managers (CircuitPython compatible).

Parameters:

- ###### **`logger`**

  (`Logger`) – Logger instance for logging messages.

- ###### **`radio_config`**

  (`RadioConfig`) – Radio configuration object.

- ###### **`**kwargs`**

  (`object`, default: `{}` ) – Hardware-specific arguments (e.g., spi, cs, rst).

Raises:

- `HardwareInitializationError` – If the radio fails to initialize after retries.

Methods:

- **`get_max_packet_size`** – Gets the maximum packet size supported by the radio.
- **`get_modulation`** – Gets the modulation mode from the initialized radio hardware.
- **`get_rssi`** – Gets the RSSI of the last received packet.
- **`modify_config`** – Modifies a specific radio configuration parameter.
- **`receive`** – Receives data from the radio.
- **`send`** – Sends data over the radio.
- **`set_modulation`** – Requests a change in the radio modulation mode.

###### get_max_packet_size

```python
get_max_packet_size() -> int

```

Gets the maximum packet size supported by the radio.

Returns:

- `int` – The maximum packet size in bytes.

###### get_modulation

```python
get_modulation() -> Type[RadioModulation]

```

Gets the modulation mode from the initialized radio hardware.

Returns:

- `Type[RadioModulation]` – The current modulation mode of the hardware.

Raises:

- `NotImplementedError` – If not implemented by subclass.

###### get_rssi

```python
get_rssi() -> int

```

Gets the RSSI of the last received packet.

Returns:

- `int` – The RSSI of the last received packet.

Raises:

- `NotImplementedError` – If not implemented by subclass.

###### modify_config

```python
modify_config(key: str, value) -> None

```

Modifies a specific radio configuration parameter.

This method must be implemented by subclasses.

Parameters:

- ###### **`key`**

  (`str`) – The configuration parameter key to modify.

- ###### **`value`**

  – The new value to set for the parameter.

Raises:

- `NotImplementedError` – If not implemented by subclass.

###### receive

```python
receive(timeout: Optional[int] = None) -> bytes | None

```

Receives data from the radio.

This method must be implemented by subclasses.

Parameters:

- ###### **`timeout`**

  (`Optional[int]`, default: `None` ) – Optional receive timeout in seconds. If None, use the default timeout.

Returns:

- `bytes | None` – The received data as bytes, or None if no data was received.

Raises:

- `NotImplementedError` – If not implemented by subclass.
- `Exception` – If receiving fails unexpectedly.

###### send

```python
send(data: bytes) -> bool

```

Sends data over the radio.

This method must be implemented by subclasses.

Parameters:

- ###### **`data`**

  (`bytes`) – The data to send.

Returns:

- `bool` – True if the data was sent successfully, False otherwise.

###### set_modulation

```python
set_modulation(modulation: Type[RadioModulation]) -> None

```

Requests a change in the radio modulation mode.

This change might take effect immediately or after a reset, depending on implementation.

Parameters:

- ###### **`modulation`**

  (`Type[RadioModulation]`) – The desired modulation mode.

##### rfm9x

This module provides a manager for RFM9x radios.

This module defines the `RFM9xManager` class, which implements the `RadioProto` interface for RFM9x radios. It handles the initialization and configuration of the radio, as well as sending and receiving data.

**Usage:**

```python
logger = Logger()
radio_config = RadioConfig()
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
reset = digitalio.DigitalInOut(board.D6)
rfm9x_manager = RFM9xManager(logger, radio_config, spi, cs, reset)
rfm9x_manager.send(b"Hello world!")

```

Classes:

- **`RFM9xManager`** – Manages RFM9x radios, implementing the RadioProto interface.

###### RFM9xManager

```python
RFM9xManager(logger: Logger, radio_config: RadioConfig, spi: SPI, chip_select: DigitalInOut, reset: DigitalInOut)

```

Bases: `BaseRadioManager`, `TemperatureSensorProto`

Manages RFM9x radios, implementing the RadioProto interface.

Parameters:

- ###### **`logger`**

  (`Logger`) – Logger instance for logging messages.

- ###### **`radio_config`**

  (`RadioConfig`) – Radio configuration object.

- ###### **`spi`**

  (`SPI`) – The SPI bus connected to the chip.

- ###### **`chip_select`**

  (`DigitalInOut`) – A DigitalInOut object connected to the chip's CS/chip select line.

- ###### **`reset`**

  (`DigitalInOut`) – A DigitalInOut object connected to the chip's RST/reset line.

Raises:

- `HardwareInitializationError` – If the radio fails to initialize after retries.

Methods:

- **`get_max_packet_size`** – Gets the maximum packet size supported by the radio.
- **`get_modulation`** – Gets the modulation mode from the initialized RFM9x radio.
- **`get_rssi`** – Gets the RSSI of the last received packet.
- **`get_temperature`** – Gets the temperature reading from the radio sensor.
- **`modify_config`** – Modifies a specific radio configuration parameter.
- **`receive`** – Receives data from the radio.
- **`send`** – Sends data over the radio.
- **`set_modulation`** – Requests a change in the radio modulation mode.

###### get_max_packet_size

```python
get_max_packet_size() -> int

```

Gets the maximum packet size supported by the radio.

Returns:

- `int` – The maximum packet size in bytes.

###### get_modulation

```python
get_modulation() -> Type[RadioModulation]

```

Gets the modulation mode from the initialized RFM9x radio.

Returns:

- `Type[RadioModulation]` – The current modulation mode of the hardware.

###### get_rssi

```python
get_rssi() -> int

```

Gets the RSSI of the last received packet.

Returns:

- `int` – The RSSI of the last received packet.

###### get_temperature

```python
get_temperature() -> float

```

Gets the temperature reading from the radio sensor.

Returns:

- `float` – The temperature in degrees Celsius.

###### modify_config

```python
modify_config(key: str, value) -> None

```

Modifies a specific radio configuration parameter.

Parameters:

- ###### **`key`**

  (`str`) – The configuration parameter key to modify.

- ###### **`value`**

  – The new value to set for the parameter.

Raises:

- `ValueError` – If the key is not recognized or invalid for the current radio type.

###### receive

```python
receive(timeout: Optional[int] = None) -> bytes | None

```

Receives data from the radio.

Parameters:

- ###### **`timeout`**

  (`Optional[int]`, default: `None` ) – Optional receive timeout in seconds. If None, use the default timeout.

Returns:

- `bytes | None` – The received data as bytes, or None if no data was received.

###### send

```python
send(data: bytes) -> bool

```

Sends data over the radio.

This method must be implemented by subclasses.

Parameters:

- ###### **`data`**

  (`bytes`) – The data to send.

Returns:

- `bool` – True if the data was sent successfully, False otherwise.

###### set_modulation

```python
set_modulation(modulation: Type[RadioModulation]) -> None

```

Requests a change in the radio modulation mode.

This change might take effect immediately or after a reset, depending on implementation.

Parameters:

- ###### **`modulation`**

  (`Type[RadioModulation]`) – The desired modulation mode.

##### sx126x

This module provides a manager for SX126x radios.

This module defines the `SX126xManager` class, which implements the `RadioProto` interface for SX126x radios. It handles the initialization and configuration of the radio, as well as sending and receiving data.

**Usage:**

```python
logger = Logger()
radio_config = RadioConfig()
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
irq = digitalio.DigitalInOut(board.D6)
reset = digitalio.DigitalInOut(board.D7)
gpio = digitalio.DigitalInOut(board.D8)
sx126x_manager = SX126xManager(logger, radio_config, spi, cs, irq, reset, gpio)
sx126x_manager.send(b"Hello world!")

```

Classes:

- **`SX126xManager`** – Manages SX126x radios, implementing the RadioProto interface.

###### SX126xManager

```python
SX126xManager(logger: Logger, radio_config: RadioConfig, spi: SPI, chip_select: DigitalInOut, irq: DigitalInOut, reset: DigitalInOut, gpio: DigitalInOut)

```

Bases: `BaseRadioManager`

Manages SX126x radios, implementing the RadioProto interface.

Parameters:

- ###### **`logger`**

  (`Logger`) – Logger instance for logging messages.

- ###### **`radio_config`**

  (`RadioConfig`) – Radio configuration object.

- ###### **`spi`**

  (`SPI`) – The SPI bus connected to the chip.

- ###### **`chip_select`**

  (`DigitalInOut`) – Chip select pin.

- ###### **`irq`**

  (`DigitalInOut`) – Interrupt request pin.

- ###### **`reset`**

  (`DigitalInOut`) – Reset pin.

- ###### **`gpio`**

  (`DigitalInOut`) – General purpose IO pin (used by SX126x).

Raises:

- `HardwareInitializationError` – If the radio fails to initialize after retries.

Methods:

- **`get_max_packet_size`** – Gets the maximum packet size supported by the radio.
- **`get_modulation`** – Gets the modulation mode from the initialized SX126x radio.
- **`get_rssi`** – Gets the RSSI of the last received packet.
- **`modify_config`** – Modifies a specific radio configuration parameter.
- **`receive`** – Receives data from the radio.
- **`send`** – Sends data over the radio.
- **`set_modulation`** – Requests a change in the radio modulation mode.

###### get_max_packet_size

```python
get_max_packet_size() -> int

```

Gets the maximum packet size supported by the radio.

Returns:

- `int` – The maximum packet size in bytes.

###### get_modulation

```python
get_modulation() -> Type[RadioModulation]

```

Gets the modulation mode from the initialized SX126x radio.

Returns:

- `Type[RadioModulation]` – The current modulation mode of the hardware.

###### get_rssi

```python
get_rssi() -> int

```

Gets the RSSI of the last received packet.

Returns:

- `int` – The RSSI of the last received packet.

Raises:

- `NotImplementedError` – If not implemented by subclass.

###### modify_config

```python
modify_config(key: str, value) -> None

```

Modifies a specific radio configuration parameter.

This method must be implemented by subclasses.

Parameters:

- ###### **`key`**

  (`str`) – The configuration parameter key to modify.

- ###### **`value`**

  – The new value to set for the parameter.

Raises:

- `NotImplementedError` – If not implemented by subclass.

###### receive

```python
receive(timeout: Optional[int] = None) -> bytes | None

```

Receives data from the radio.

Parameters:

- ###### **`timeout`**

  (`Optional[int]`, default: `None` ) – Optional receive timeout in seconds. If None, use the default timeout.

Returns:

- `bytes | None` – The received data as bytes, or None if no data was received.

###### send

```python
send(data: bytes) -> bool

```

Sends data over the radio.

This method must be implemented by subclasses.

Parameters:

- ###### **`data`**

  (`bytes`) – The data to send.

Returns:

- `bool` – True if the data was sent successfully, False otherwise.

###### set_modulation

```python
set_modulation(modulation: Type[RadioModulation]) -> None

```

Requests a change in the radio modulation mode.

This change might take effect immediately or after a reset, depending on implementation.

Parameters:

- ###### **`modulation`**

  (`Type[RadioModulation]`) – The desired modulation mode.

##### sx1280

This module provides a manager for SX1280 radios.

This module defines the `SX1280Manager` class, which implements the `RadioProto` interface for SX1280 radios. It handles the initialization and configuration of the radio, as well as sending and receiving data.

**Usage:**

```python
logger = Logger()
radio_config = RadioConfig()
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
reset = digitalio.DigitalInOut(board.D6)
busy = digitalio.DigitalInOut(board.D7)
txen = digitalio.DigitalInOut(board.D8)
rxen = digitalio.DigitalInOut(board.D9)
sx1280_manager = SX1280Manager(logger, radio_config, spi, cs, reset, busy, 2400.0, txen, rxen)
sx1280_manager.send(b"Hello world!")

```

Classes:

- **`SX1280Manager`** – Manages SX1280 radios, implementing the RadioProto interface.

###### SX1280Manager

```python
SX1280Manager(logger: Logger, radio_config: RadioConfig, spi: SPI, chip_select: DigitalInOut, reset: DigitalInOut, busy: DigitalInOut, frequency: float, txen: DigitalInOut, rxen: DigitalInOut)

```

Bases: `BaseRadioManager`

Manages SX1280 radios, implementing the RadioProto interface.

Parameters:

- ###### **`logger`**

  (`Logger`) – Logger instance for logging messages.

- ###### **`radio_config`**

  (`RadioConfig`) – Radio configuration object.

- ###### **`spi`**

  (`SPI`) – The SPI bus connected to the chip.

- ###### **`chip_select`**

  (`DigitalInOut`) – Chip select pin.

- ###### **`reset`**

  (`DigitalInOut`) – Reset pin.

- ###### **`busy`**

  (`DigitalInOut`) – Busy pin.

- ###### **`frequency`**

  (`float`) – The frequency to operate on.

- ###### **`txen`**

  (`DigitalInOut`) – Transmit enable pin.

- ###### **`rxen`**

  (`DigitalInOut`) – Receive enable pin.

Methods:

- **`get_max_packet_size`** – Gets the maximum packet size supported by the radio.
- **`get_modulation`** – Gets the modulation mode from the initialized SX1280 radio.
- **`get_rssi`** – Gets the RSSI of the last received packet.
- **`modify_config`** – Modifies a specific radio configuration parameter.
- **`receive`** – Receives data from the radio.
- **`send`** – Sends data over the radio.
- **`set_modulation`** – Requests a change in the radio modulation mode.

###### get_max_packet_size

```python
get_max_packet_size() -> int

```

Gets the maximum packet size supported by the radio.

Returns:

- `int` – The maximum packet size in bytes.

###### get_modulation

```python
get_modulation() -> Type[RadioModulation]

```

Gets the modulation mode from the initialized SX1280 radio.

Returns:

- `Type[RadioModulation]` – The current modulation mode of the hardware.

###### get_rssi

```python
get_rssi() -> int

```

Gets the RSSI of the last received packet.

Returns:

- `int` – The RSSI of the last received packet.

Raises:

- `NotImplementedError` – If not implemented by subclass.

###### modify_config

```python
modify_config(key: str, value) -> None

```

Modifies a specific radio configuration parameter.

This method must be implemented by subclasses.

Parameters:

- ###### **`key`**

  (`str`) – The configuration parameter key to modify.

- ###### **`value`**

  – The new value to set for the parameter.

Raises:

- `NotImplementedError` – If not implemented by subclass.

###### receive

```python
receive(timeout: Optional[int] = None) -> bytes | None

```

Receives data from the radio.

Parameters:

- ###### **`timeout`**

  (`Optional[int]`, default: `None` ) – Optional receive timeout in seconds. If None, use the default timeout.

Returns:

- `bytes | None` – The received data as bytes, or None if no data was received.

###### send

```python
send(data: bytes) -> bool

```

Sends data over the radio.

This method must be implemented by subclasses.

Parameters:

- ###### **`data`**

  (`bytes`) – The data to send.

Returns:

- `bool` – True if the data was sent successfully, False otherwise.

###### set_modulation

```python
set_modulation(modulation: Type[RadioModulation]) -> None

```

Requests a change in the radio modulation mode.

This change might take effect immediately or after a reset, depending on implementation.

Parameters:

- ###### **`modulation`**

  (`Type[RadioModulation]`) – The desired modulation mode.

#### modulation

This module defines the available radio modulation types.

This module provides a set of classes that represent the different radio modulation types that can be used by the radio hardware. These classes are used to configure the radio and to identify the current modulation type.

Classes:

- **`FSK`** – Represents the FSK modulation mode.
- **`LoRa`** – Represents the LoRa modulation mode.
- **`RadioModulation`** – Base class for radio modulation modes.

##### FSK

Bases: `RadioModulation`

Represents the FSK modulation mode.

##### LoRa

Bases: `RadioModulation`

Represents the LoRa modulation mode.

##### RadioModulation

Base class for radio modulation modes.

#### packetizer

This package provides an interface for packetizing data for radio communication.

Modules:

- **`packet_manager`** – This module provides a PacketManager for sending and receiving data over a radio.

##### packet_manager

This module provides a PacketManager for sending and receiving data over a radio.

This module handles the fragmentation and reassembly of data into packets for transmission over a radio. It also provides methods for sending and receiving acknowledgments.

**Usage:**

```python
logger = Logger()
radio = RFM9xManager(logger, radio_config, spi, cs, reset)
packet_manager = PacketManager(logger, radio, "my_license_key")
packet_manager.send(b"Hello world!")
received_data = packet_manager.listen()

```

Classes:

- **`PacketManager`** – Manages the sending and receiving of data packets over a radio.

###### PacketManager

```python
PacketManager(logger: Logger, radio: RadioProto, license: str, message_counter: Counter, send_delay: float = 0.2)

```

Manages the sending and receiving of data packets over a radio.

Parameters:

- ###### **`logger`**

  (`Logger`) – The logger to use.

- ###### **`radio`**

  (`RadioProto`) – The radio instance to use for communication.

- ###### **`license`**

  (`str`) – The license key for sending data.

- ###### **`send_delay`**

  (`float`, default: `0.2` ) – The delay between sending packets.

Methods:

- **`listen`** – Listens for data from the radio.
- **`send`** – Sends data over the radio.
- **`send_acknowledgement`** – Sends an acknowledgment to the radio.

###### listen

```python
listen(timeout: Optional[int] = None) -> bytes | None

```

Listens for data from the radio.

Parameters:

- ###### **`timeout`**

  (`Optional[int]`, default: `None` ) – Optional receive timeout in seconds. If None, use the default timeout.

Returns:

- `bytes | None` – The received data as bytes, or None if no data was received.

###### send

```python
send(data: bytes) -> bool

```

Sends data over the radio.

Parameters:

- ###### **`data`**

  (`bytes`) – The data to send.

Returns:

- `bool` – True if the data was sent successfully, False otherwise.

###### send_acknowledgement

```python
send_acknowledgement() -> None

```

Sends an acknowledgment to the radio.

## logger

This module provides a Logger class for handling logging messages.

The Logger class supports different severity levels, colorized output, and error counting. Logs are formatted as JSON and can be output to the console.

**Usage:**

```python
error_counter = Counter(nvm)
logger = Logger(error_counter, log_level=LogLevel.INFO, colorized=True)
logger.info("This is an informational message.")
logger.error("This is an error message.", err=Exception("Something went wrong."))

```

Classes:

- **`LogLevel`** – Defines log level constants for Logger.
- **`Logger`** – Handles logging messages with different severity levels.

### LogLevel

Defines log level constants for Logger.

### Logger

```python
Logger(error_counter: Counter, log_level: int = NOTSET, colorized: bool = False)

```

Handles logging messages with different severity levels.

Parameters:

- #### **`error_counter`**

  (`Counter`) – Counter for error occurrences.

- #### **`log_level`**

  (`int`, default: `NOTSET` ) – Initial log level.

- #### **`colorized`**

  (`bool`, default: `False` ) – Whether to colorize output.

Methods:

- **`critical`** – Log a message with severity level CRITICAL.
- **`debug`** – Log a message with severity level DEBUG.
- **`error`** – Log a message with severity level ERROR.
- **`get_error_count`** – Returns the current error count.
- **`info`** – Log a message with severity level INFO.
- **`warning`** – Log a message with severity level WARNING.

#### critical

```python
critical(message: str, err: Exception, **kwargs: object) -> None

```

Log a message with severity level CRITICAL.

Parameters:

- ##### **`message`**

  (`str`) – The log message.

- ##### **`err`**

  (`Exception`) – The exception to log.

- ##### **`**kwargs`**

  (`object`, default: `{}` ) – Additional key/value pairs to include in the log.

#### debug

```python
debug(message: str, **kwargs: object) -> None

```

Log a message with severity level DEBUG.

Parameters:

- ##### **`message`**

  (`str`) – The log message.

- ##### **`**kwargs`**

  (`object`, default: `{}` ) – Additional key/value pairs to include in the log.

#### error

```python
error(message: str, err: Exception, **kwargs: object) -> None

```

Log a message with severity level ERROR.

Parameters:

- ##### **`message`**

  (`str`) – The log message.

- ##### **`err`**

  (`Exception`) – The exception to log.

- ##### **`**kwargs`**

  (`object`, default: `{}` ) – Additional key/value pairs to include in the log.

#### get_error_count

```python
get_error_count() -> int

```

Returns the current error count.

Returns:

- **`int`** ( `int` ) – The number of errors logged.

#### info

```python
info(message: str, **kwargs: object) -> None

```

Log a message with severity level INFO.

Parameters:

- ##### **`message`**

  (`str`) – The log message.

- ##### **`**kwargs`**

  (`object`, default: `{}` ) – Additional key/value pairs to include in the log.

#### warning

```python
warning(message: str, **kwargs: object) -> None

```

Log a message with severity level WARNING.

Parameters:

- ##### **`message`**

  (`str`) – The log message.

- ##### **`**kwargs`**

  (`object`, default: `{}` ) – Additional key/value pairs to include in the log.

## nvm

The NVM package is a collection of functionality that interacts with non-volatile memory

Modules:

- **`counter`** – This module provides the Counter class for managing 8-bit counters stored in
- **`flag`** – This module provides the Flag class for managing boolean flags stored in

### counter

This module provides the Counter class for managing 8-bit counters stored in non-volatile memory (NVM) on CircuitPython devices.

Classes:

- **`Counter`** – Counter class for managing 8-bit counters stored in non-volatile memory.

#### Counter

```python
Counter(index: int)

```

Counter class for managing 8-bit counters stored in non-volatile memory.

Attributes:

- **`_index`** (`int`) – The index of the counter in the NVM datastore.
- **`_datastore`** (`ByteArray`) – The NVM datastore.

Parameters:

- ##### **`index`**

  (`int`) – The index of the counter in the datastore.

Raises:

- `ValueError` – If NVM is not available.

Methods:

- **`get`** – Returns the value of the counter.
- **`get_name`** – get_name returns the name of the counter
- **`increment`** – Increases the counter by one, with 8-bit rollover.

##### get

```python
get() -> int

```

Returns the value of the counter.

Returns:

- **`int`** ( `int` ) – The current value of the counter.

##### get_name

```python
get_name() -> str

```

get_name returns the name of the counter

##### increment

```python
increment() -> None

```

Increases the counter by one, with 8-bit rollover.

### flag

This module provides the Flag class for managing boolean flags stored in non-volatile memory (NVM) on CircuitPython devices.

Classes:

- **`Flag`** – Flag class for managing boolean flags stored in non-volatile memory.

#### Flag

```python
Flag(index: int, bit_index: int)

```

Flag class for managing boolean flags stored in non-volatile memory.

Attributes:

- **`_index`** (`int`) – The index of the flag (byte) in the NVM datastore.
- **`_bit`** (`int`) – The bit index within the byte.
- **`_datastore`** (`ByteArray`) – The NVM datastore.
- **`_bit_mask`** (`int`) – Bitmask for the flag's bit position.

Parameters:

- ##### **`index`**

  (`int`) – The index of the flag (byte) in the datastore.

- ##### **`bit_index`**

  (`int`) – The index of the bit within the byte.

Raises:

- `ValueError` – If NVM is not available.

Methods:

- **`get`** – Returns the value of the flag.
- **`get_name`** – get_name returns the name of the flag
- **`toggle`** – Sets or clears the flag value.

##### get

```python
get() -> bool

```

Returns the value of the flag.

Returns:

- **`bool`** ( `bool` ) – The current value of the flag.

##### get_name

```python
get_name() -> str

```

get_name returns the name of the flag

##### toggle

```python
toggle(value: bool) -> None

```

Sets or clears the flag value.

Parameters:

- ###### **`value`**

  (`bool`) – If True, sets the flag; if False, clears the flag.

## power_health

This module provides a PowerHealth class for monitoring the power system.

The PowerHealth class checks the battery voltage and current draw to determine the overall health of the power system. It returns one of four states: NOMINAL, DEGRADED, CRITICAL, or UNKNOWN.

**Usage:**

```python
logger = Logger()
config = Config("config.json")
power_monitor = INA219Manager(logger, i2c)
power_health = PowerHealth(logger, config, power_monitor)
health_status = power_health.get()

```

Classes:

- **`CRITICAL`** – Represents a critical power health state.
- **`DEGRADED`** – Represents a degraded power health state.
- **`NOMINAL`** – Represents a nominal power health state.
- **`PowerHealth`** – Monitors the power system and determines its health.
- **`State`** – Base class for power health states.
- **`UNKNOWN`** – Represents an unknown power health state.

### CRITICAL

Bases: `State`

Represents a critical power health state.

### DEGRADED

Bases: `State`

Represents a degraded power health state.

### NOMINAL

Bases: `State`

Represents a nominal power health state.

### PowerHealth

```python
PowerHealth(logger: Logger, config: Config, power_monitor: PowerMonitorProto)

```

Monitors the power system and determines its health.

Parameters:

- #### **`logger`**

  (`Logger`) – The logger to use.

- #### **`config`**

  (`Config`) – The configuration to use.

- #### **`power_monitor`**

  (`PowerMonitorProto`) – The power monitor to use.

Methods:

- **`get`** – Gets the current power health.

#### get

```python
get() -> NOMINAL | DEGRADED | CRITICAL | UNKNOWN

```

Gets the current power health.

Returns:

- `NOMINAL | DEGRADED | CRITICAL | UNKNOWN` – The current power health state.

### State

Base class for power health states.

### UNKNOWN

Bases: `State`

Represents an unknown power health state.

## protos

This module defines hardware agnostic protocols for accessing devices with certain features. This allows for flexibility in the design of the system, enabling the use of different hardware implementations without changing the code that uses them.

CircuitPython does not support Protocols directly, but these classes can still be used to define an interface for type checking and ensuring multi-device compatibility.

https://docs.python.org/3/library/typing.html#typing.Protocol

Modules:

- **`burnwire`** – This protocol specifies the interface that any burnwire implementation must adhere
- **`imu`** – This protocol specifies the interface that any IMU implementation must adhere to,
- **`magnetometer`** – This protocol specifies the interface that any magnetometer implementation must
- **`power_monitor`** – This protocol specifies the interface that any power monitor implementation must
- **`radio`** – This protocol specifies the interface that any radio implementation must adhere
- **`rtc`** – This protocol specifies the interface that any Real-Time Clock (RTC) implementation
- **`temperature_sensor`** – This protocol specifies the interface that any temperature sensor implementation

### burnwire

This protocol specifies the interface that any burnwire implementation must adhere to, ensuring consistent behavior across different burnwire hardware.

Classes:

- **`BurnwireProto`** – Protocol defining the interface for a burnwire port.

#### BurnwireProto

Protocol defining the interface for a burnwire port.

Methods:

- **`burn`** – Fires the burnwire for a specified amount of time.

##### burn

```python
burn(timeout_duration: float) -> bool

```

Fires the burnwire for a specified amount of time.

Parameters:

- ###### **`timeout_duration`**

  (`float`) – The maximum amount of time to keep the burnwire on.

Returns:

- `bool` – True if the burn occurred successfully, False otherwise.

Raises:

- `Exception` – If there is an error toggling the burnwire pins.

### imu

This protocol specifies the interface that any IMU implementation must adhere to, ensuring consistent behavior across different IMU hardware.

Classes:

- **`IMUProto`** – Protocol defining the interface for an Inertial Measurement Unit (IMU).

#### IMUProto

Protocol defining the interface for an Inertial Measurement Unit (IMU).

Methods:

- **`get_acceleration`** – Gets the acceleration data from the inertial measurement unit.
- **`get_gyro_data`** – Gets the gyroscope data from the inertial measurement unit.

##### get_acceleration

```python
get_acceleration() -> tuple[float, float, float] | None

```

Gets the acceleration data from the inertial measurement unit.

Returns:

- `tuple[float, float, float] | None` – A tuple containing the x, y, and z acceleration values in m/s^2, or
- `tuple[float, float, float] | None` – None if not available.

Raises:

- `Exception` – If there is an error retrieving the values.

##### get_gyro_data

```python
get_gyro_data() -> tuple[float, float, float] | None

```

Gets the gyroscope data from the inertial measurement unit.

Returns:

- `tuple[float, float, float] | None` – A tuple containing the x, y, and z angular acceleration values in
- `tuple[float, float, float] | None` – radians per second, or None if not available.

Raises:

- `Exception` – If there is an error retrieving the values.

### magnetometer

This protocol specifies the interface that any magnetometer implementation must adhere to, ensuring consistent behavior across different magnetometer hardware.

Classes:

- **`MagnetometerProto`** – Protocol defining the interface for a Magnetometer.

#### MagnetometerProto

Protocol defining the interface for a Magnetometer.

Methods:

- **`get_vector`** – Gets the magnetic field vector from the magnetometer.

##### get_vector

```python
get_vector() -> tuple[float, float, float] | None

```

Gets the magnetic field vector from the magnetometer.

Returns:

- `tuple[float, float, float] | None` – A tuple containing the x, y, and z magnetic field values in Gauss, or
- `tuple[float, float, float] | None` – None if not available.

Raises:

- `Exception` – If there is an error retrieving the values.

### power_monitor

This protocol specifies the interface that any power monitor implementation must adhere to, ensuring consistent behavior across different power monitor hardware.

Classes:

- **`PowerMonitorProto`** – Protocol defining the interface for a Power Monitor.

#### PowerMonitorProto

Protocol defining the interface for a Power Monitor.

Methods:

- **`get_bus_voltage`** – Gets the bus voltage from the power monitor.
- **`get_current`** – Gets the current from the power monitor.
- **`get_shunt_voltage`** – Gets the shunt voltage from the power monitor.

##### get_bus_voltage

```python
get_bus_voltage() -> float | None

```

Gets the bus voltage from the power monitor.

Returns:

- `float | None` – The bus voltage in volts, or None if not available.

##### get_current

```python
get_current() -> float | None

```

Gets the current from the power monitor.

Returns:

- `float | None` – The current in amps, or None if not available.

##### get_shunt_voltage

```python
get_shunt_voltage() -> float | None

```

Gets the shunt voltage from the power monitor.

Returns:

- `float | None` – The shunt voltage in volts, or None if not available.

### radio

This protocol specifies the interface that any radio implementation must adhere to, ensuring consistent behavior across different radio hardware.

Classes:

- **`RadioProto`** – Protocol defining the interface for a radio.

#### RadioProto

Protocol defining the interface for a radio.

Methods:

- **`get_max_packet_size`** – Gets the maximum packet size supported by the radio.
- **`get_modulation`** – Gets the currently configured or active radio modulation mode.
- **`get_rssi`** – Gets the RSSI of the last received packet.
- **`modify_config`** – Modifies a specific radio configuration parameter.
- **`receive`** – Receives data from the radio.
- **`send`** – Sends data over the radio.
- **`set_modulation`** – Requests a change in the radio modulation mode.

##### get_max_packet_size

```python
get_max_packet_size() -> int

```

Gets the maximum packet size supported by the radio.

Returns:

- `int` – The maximum packet size in bytes.

##### get_modulation

```python
get_modulation() -> Type[RadioModulation]

```

Gets the currently configured or active radio modulation mode.

Returns:

- `Type[RadioModulation]` – The current modulation mode.

##### get_rssi

```python
get_rssi() -> int

```

Gets the RSSI of the last received packet.

Returns:

- `int` – The RSSI value in dBm.

Raises:

- `NotImplementedError` – If not implemented by subclass.

##### modify_config

```python
modify_config(key: str, value) -> None

```

Modifies a specific radio configuration parameter.

Parameters:

- ###### **`key`**

  (`str`) – The configuration parameter key to modify.

- ###### **`value`**

  – The new value to set for the parameter.

Raises:

- `NotImplementedError` – If not implemented by subclass.

##### receive

```python
receive(timeout: Optional[int] = None) -> Optional[bytes]

```

Receives data from the radio.

Parameters:

- ###### **`timeout`**

  (`Optional[int]`, default: `None` ) – Optional receive timeout in seconds. If None, use the default timeout.

Returns:

- `Optional[bytes]` – The received data as bytes, or None if no data was received.

##### send

```python
send(data: bytes) -> bool

```

Sends data over the radio.

Parameters:

- ###### **`data`**

  (`bytes`) – The data to send.

Returns:

- `bool` – True if the send was successful, False otherwise.

##### set_modulation

```python
set_modulation(modulation: Type[RadioModulation]) -> None

```

Requests a change in the radio modulation mode.

This change might take effect immediately or after a reset, depending on implementation.

Parameters:

- ###### **`modulation`**

  (`Type[RadioModulation]`) – The desired modulation mode.

### rtc

This protocol specifies the interface that any Real-Time Clock (RTC) implementation must adhere to, ensuring consistent behavior across different RTC hardware.

Classes:

- **`RTCProto`** – Protocol defining the interface for a Real Time Clock (RTC).

#### RTCProto

Protocol defining the interface for a Real Time Clock (RTC).

Methods:

- **`set_time`** – Sets the time on the real-time clock.

##### set_time

```python
set_time(year: int, month: int, date: int, hour: int, minute: int, second: int, weekday: int) -> None

```

Sets the time on the real-time clock.

Parameters:

- ###### **`year`**

  (`int`) – The year value (0-9999).

- ###### **`month`**

  (`int`) – The month value (1-12).

- ###### **`date`**

  (`int`) – The date value (1-31).

- ###### **`hour`**

  (`int`) – The hour value (0-23).

- ###### **`minute`**

  (`int`) – The minute value (0-59).

- ###### **`second`**

  (`int`) – The second value (0-59).

- ###### **`weekday`**

  (`int`) – The nth day of the week (0-6), where 0 represents Sunday and 6 represents Saturday.

Raises:

- `Exception` – If there is an error setting the values.

### temperature_sensor

This protocol specifies the interface that any temperature sensor implementation must adhere to, ensuring consistent behavior across different temperature sensor hardware.

Classes:

- **`TemperatureSensorProto`** – Protocol defining the interface for a temperature sensor.

#### TemperatureSensorProto

Protocol defining the interface for a temperature sensor.

Methods:

- **`get_temperature`** – Gets the temperature reading of the sensor.

##### get_temperature

```python
get_temperature() -> float | None

```

Gets the temperature reading of the sensor.

Returns:

- `float | None` – The temperature in degrees Celsius, or None if not available.

## rtc

This module provides Real-Time Clock (RTC) management functionality for the PySquared satellite.

Modules:

- **`manager`** – This module provides the managers for various Real-Time Clock (RTC) implementations

### manager

This module provides the managers for various Real-Time Clock (RTC) implementations

Modules:

- **`microcontroller`** – This module provides a manager for the Microcontroller's Real-Time Clock (RTC).
- **`rv3028`** – This module provides a manager for the RV3028 Real-Time Clock (RTC).

#### microcontroller

This module provides a manager for the Microcontroller's Real-Time Clock (RTC).

This module defines the `MicrocontrollerManager` class, which provides an interface for interacting with the microcontroller's built-in RTC. It allows for setting the current time.

**Usage:**

```python
rtc_manager = MicrocontrollerManager()
rtc_manager.set_time(2024, 7, 8, 10, 30, 0, 1) # Set to July 8, 2024, 10:30:00 AM, Monday

```

Classes:

- **`MicrocontrollerManager`** – Manages the Microcontroller's Real Time Clock (RTC).

##### MicrocontrollerManager

```python
MicrocontrollerManager()

```

Bases: `RTCProto`

Manages the Microcontroller's Real Time Clock (RTC).

This method is required on every boot to ensure the RTC is ready for use.

Methods:

- **`set_time`** – Updates the Microcontroller's Real Time Clock (RTC).

###### set_time

```python
set_time(year: int, month: int, date: int, hour: int, minute: int, second: int, weekday: int) -> None

```

Updates the Microcontroller's Real Time Clock (RTC).

Parameters:

- ###### **`year`**

  (`int`) – The year value (0-9999).

- ###### **`month`**

  (`int`) – The month value (1-12).

- ###### **`date`**

  (`int`) – The date value (1-31).

- ###### **`hour`**

  (`int`) – The hour value (0-23).

- ###### **`minute`**

  (`int`) – The minute value (0-59).

- ###### **`second`**

  (`int`) – The second value (0-59).

- ###### **`weekday`**

  (`int`) – The nth day of the week (0-6), where 0 represents Sunday and 6 represents Saturday.

#### rv3028

This module provides a manager for the RV3028 Real-Time Clock (RTC).

This module defines the `RV3028Manager` class, which provides a high-level interface for interacting with the RV3028 RTC. It handles the initialization of the sensor and provides methods for setting the current time.

**Usage:**

```python
logger = Logger()
i2c = busio.I2C(board.SCL, board.SDA)
rtc_manager = RV3028Manager(logger, i2c)
rtc_manager.set_time(2024, 7, 8, 10, 30, 0, 1) # Set to July 8, 2024, 10:30:00 AM, Monday

```

Classes:

- **`RV3028Manager`** – Manages the RV3028 RTC.

##### RV3028Manager

```python
RV3028Manager(logger: Logger, i2c: I2C)

```

Bases: `RTCProto`

Manages the RV3028 RTC.

Parameters:

- ###### **`logger`**

  (`Logger`) – The logger to use.

- ###### **`i2c`**

  (`I2C`) – The I2C bus connected to the chip.

Raises:

- `HardwareInitializationError` – If the RTC fails to initialize.

Methods:

- **`set_time`** – Sets the time on the real-time clock.

###### set_time

```python
set_time(year: int, month: int, date: int, hour: int, minute: int, second: int, weekday: int) -> None

```

Sets the time on the real-time clock.

Parameters:

- ###### **`year`**

  (`int`) – The year value (0-9999).

- ###### **`month`**

  (`int`) – The month value (1-12).

- ###### **`date`**

  (`int`) – The date value (1-31).

- ###### **`hour`**

  (`int`) – The hour value (0-23).

- ###### **`minute`**

  (`int`) – The minute value (0-59).

- ###### **`second`**

  (`int`) – The second value (0-59).

- ###### **`weekday`**

  (`int`) – The nth day of the week (0-6), where 0 represents Sunday and 6 represents Saturday.

Raises:

- `Exception` – If there is an error setting the values.

## sleep_helper

This module provides the SleepHelper class for managing safe sleep and hibernation modes for the PySquared satellite. It ensures the satellite sleeps for specified durations while maintaining system safety and watchdog activity.

Classes:

- **`SleepHelper`** – Class responsible for sleeping the Satellite to conserve power.

### SleepHelper

```python
SleepHelper(logger: Logger, config: Config, watchdog: Watchdog)

```

Class responsible for sleeping the Satellite to conserve power.

Attributes:

- **`cubesat`** (`Satellite`) – The Satellite object.
- **`logger`** (`Logger`) – Logger instance for logging events and errors.
- **`watchdog`** (`Watchdog`) – Watchdog instance for system safety.
- **`config`** (`Config`) – Configuration object.

Parameters:

- #### **`logger`**

  (`Logger`) – Logger instance for logging events and errors.

- #### **`watchdog`**

  (`Watchdog`) – Watchdog instance for system safety.

- #### **`config`**

  (`Config`) – Configuration object.

Methods:

- **`safe_sleep`** – Puts the Satellite to sleep for a specified duration, in seconds.

#### safe_sleep

```python
safe_sleep(duration) -> None

```

Puts the Satellite to sleep for a specified duration, in seconds.

Allows for a maximum sleep duration of the longest_allowable_sleep_time field specified in config

Parameters:

- ##### **`duration`**

  (`int`) – Specified time, in seconds, to sleep the Satellite for.

## watchdog

This module provides the Watchdog class for managing the hardware watchdog timer on the PySquared satellite. The watchdog helps ensure system reliability by requiring periodic "petting" to prevent system resets.

Classes:

- **`Watchdog`** – Watchdog class for managing the hardware watchdog timer.

### Watchdog

```python
Watchdog(logger: Logger, pin: Pin)

```

Watchdog class for managing the hardware watchdog timer.

Attributes:

- **`_log`** (`Logger`) – Logger instance for logging messages.
- **`_digital_in_out`** (`DigitalInOut`) – Digital output for controlling the watchdog pin.

Parameters:

- #### **`logger`**

  (`Logger`) – Logger instance for logging messages.

- #### **`pin`**

  (`Pin`) – Pin to use for the watchdog timer.

Raises:

- `HardwareInitializationError` – If the pin fails to initialize.

Methods:

- **`pet`** – Pets (resets) the watchdog timer to prevent system reset.

#### pet

```python
pet() -> None

```

Pets (resets) the watchdog timer to prevent system reset.
