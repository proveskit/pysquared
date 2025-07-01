# Load Switch Manager

The Load Switch Manager provides a consistent interface for controlling load switches on PySquared satellite hardware. Load switches are used to control power to various subsystems and components.

## Overview

The `LoadSwitchManager` class implements the `LoadSwitchProto` interface and provides:

- Individual switch control (turn on/off specific switches)
- Bulk operations (turn all switches on/off)
- State tracking (public dictionary of switch states)
- Dynamic switch management (add/remove switches at runtime)
- Custom naming for each load switch
- Configurable enable logic (active high/low)

## Usage

### Basic Setup

```python
from lib.pysquared.hardware.load_switch.manager.load_switch import LoadSwitchManager
from digitalio import DigitalInOut
import board

# Define your load switches with custom names
load_switches = {
    "radio": DigitalInOut(board.RADIO_ENABLE),
    "imu": DigitalInOut(board.IMU_ENABLE),
    "magnetometer": DigitalInOut(board.MAG_ENABLE),
    "camera": DigitalInOut(board.CAMERA_ENABLE),
}

# Initialize the manager
load_switch_manager = LoadSwitchManager(logger, load_switches, enable_logic=True)
```

### Individual Switch Control

```python
# Turn on a specific switch
success = load_switch_manager.turn_on("radio")
if success:
    print("Radio turned on successfully")

# Turn off a specific switch
success = load_switch_manager.turn_off("camera")
if success:
    print("Camera turned off successfully")
```

### Bulk Operations

```python
# Turn all switches on
success = load_switch_manager.turn_all_on()
if success:
    print("All switches turned on")

# Turn all switches off
success = load_switch_manager.turn_all_off()
if success:
    print("All switches turned off")
```

### State Monitoring

```python
# Check individual switch state
radio_state = load_switch_manager.get_switch_state("radio")
if radio_state is True:
    print("Radio is on")
elif radio_state is False:
    print("Radio is off")
else:
    print("Radio switch not found")

# Get all switch states
all_states = load_switch_manager.get_all_states()
print(f"All switch states: {all_states}")

# Access the public state dictionary directly
print(f"Radio state: {load_switch_manager.switch_states['radio']}")
```

### Dynamic Switch Management

```python
# Add a new switch at runtime
new_switch = DigitalInOut(board.NEW_DEVICE_ENABLE)
success = load_switch_manager.add_switch("new_device", new_switch)
if success:
    print("New switch added successfully")

# Remove a switch
success = load_switch_manager.remove_switch("camera")
if success:
    print("Camera switch removed")

# Get list of all switch names
switch_names = load_switch_manager.get_switch_names()
print(f"Available switches: {switch_names}")
```

## Configuration

### Enable Logic

The `enable_logic` parameter determines whether switches are activated with a high or low signal:

```python
# Active high (default) - switches turn on when pin is HIGH
manager_high = LoadSwitchManager(logger, switches, enable_logic=True)

# Active low - switches turn on when pin is LOW
manager_low = LoadSwitchManager(logger, switches, enable_logic=False)
```

## Error Handling

The LoadSwitchManager includes comprehensive error handling:

- Invalid switch names return `False` for operations
- Hardware errors are logged and return `False`
- Initialization errors raise `HardwareInitializationError`
- All operations are logged for debugging

## Interface Methods

### Required Methods (LoadSwitchProto)

- `turn_on(switch_name: str) -> bool`
- `turn_off(switch_name: str) -> bool`
- `turn_all_on() -> bool`
- `turn_all_off() -> bool`
- `get_switch_state(switch_name: str) -> bool | None`
- `get_all_states() -> Dict[str, bool]`

### Additional Methods

- `add_switch(switch_name: str, switch_pin: DigitalInOut) -> bool`
- `remove_switch(switch_name: str) -> bool`
- `get_switch_names() -> list[str]`

## Properties

- `switch_states: Dict[str, bool]` - Public dictionary tracking all switch states

## Dependencies

- `digitalio.DigitalInOut` - For pin control
- `pysquared.logger.Logger` - For logging
- `pysquared.protos.load_switch.LoadSwitchProto` - Interface definition
- `pysquared.hardware.decorators.with_retries` - For retry logic
- `pysquared.hardware.exception.HardwareInitializationError` - For error handling
