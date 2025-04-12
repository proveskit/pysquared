# Safe Device Failure

## Status

Proposed

## Context

This ADR proposes patterns allowing non-critical devices to fail while ensuring downstream services are not impacted. For example, if the IMU fails to initialize, we want to ensure that the satellite continues operation, but services such as de-tumbling can understand that the IMU is not available and adjust their behavior accordingly. In this case, the de-tumbling service would not engage magnetorquers, reaction wheels, or thrusters.

This ADR does not attempt to solve partial failures of a device where only some of its functionality is available or when it returns faulty data. This problem can be addressed in a future ADR.

### Prior Implementation
In a previous version of PySquared, each device was initialized using a `try/except` block. [A dictionary of bools](https://github.com/proveskit/pysquared/blob/c03e6ed069168f7e6c5df0c228ec86429db51e7f/lib/pysquared/pysquared.py#L226-L245) representing device initialization state was passed to each initialization function. Each device would set a key to `True` if initialized. There were various checks throughout the codebase to determine if a device was initialized before use.

### Current State
Currently, all device initialization failures are fatal, meaning that if a device fails to initialize, the entire root `try/except` in `main.py` will be triggered, and the satellite will restart. For example, the [IMU initialization](https://github.com/proveskit/CircuitPython_RP2040_v4/blob/4693e43a373030e74dad109c0858c9e36998f1df/main.py#L94) in the v4 board repo is not handling exceptions.

Possibly by accident, all current hardware device managers are safe to call after a failed initialization. As long as their initialization is wrapped in a `try/except` block, the device manager will return `None` for all subsequent calls for sensor readings.

## Proposal

### Pattern 1: Generic Device Protocol with `get_state()`

We propose to add a `get_state()` method to the generic device protocol. This method will return 1 of 3 possible states: `unknown`, `initialized`, or `failed` allowing downstream services to check the state of a device before attempting to use it.

#### Example Implementation

`protos/device.py`
```python
class DeviceState:
    unknown = 0
    initialized = 1
    failed = 2

class DeviceProto:
    def get_state(self) -> int:
        """Get the current state of the device.

        :return: The current state of the device as an integer. Possible values are:
             - 0: Unknown
             - 1: Initialized
             - 2: Error
        :rtype: int
        """
        ...
```

`imu/manager/lsm6dsox.py`
```diff
-class LSM6DSOXManager(IMUProto, TemperatureSensorProto):
+class LSM6DSOXManager(DeviceProto, IMUProto, TemperatureSensorProto):
     """Manager class for creating LIS2MDL IMU instances.
     The purpose of the manager class is to hide the complexity of IMU initialization from the caller.
     Specifically we should try to keep adafruit_lsm6ds to only this manager class.
@@ -40,9 +41,19 @@ class LSM6DSOXManager(IMUProto, TemperatureSensorProto):
         try:
             self._log.debug("Initializing IMU")
             self._imu: LSM6DSOX = LSM6DSOX(i2c, address)
+            self._state = DeviceState.initialized
         except Exception as e:
+            self._state = DeviceState.failed
             raise HardwareInitializationError("Failed to initialize IMU") from e

+    def get_state(self) -> int:
+        """Get the state of the IMU.
+
+        :return: The state of the IMU.
+        :rtype: int
+        """
+        return self._state
```

`main.py`
```py
from imu.manager.lsm6dsox import LSM6DSOXManager

# root try/except block
try:
    try:
        # Initialize the IMU
        imu = LSM6DSOXManager(i2c, address)
    except HardwareInitializationError as e:
        logger.error("Failed to initialize IMU", e)

    future_downstream_service(imu)

    # Continue with the rest of the program
```

`future_downstream_service.py`
```py
from protos.imu import IMUProto
from protos.device import DeviceState

def future_downstream_service(imu: IMUProto):
    if imu.get_state() != DeviceState.initialized:
        # Handle the case where the IMU is not initialized
        pass

    # Do something with the IMU
```

#### Pros
- Allows downstream services to check the state of a device before attempting to use it.
- State is encapsulated in the manager, and the manager is responsible for returning its state.
- State values are explicitly defined in the protocol and can be reused across all devices.

#### Neutral
- Attempting to emulate enum behavior with `DeviceState` in CircuitPython, where they are not officially supported, is not ideal.

#### Cons
- It's not obvious that the device manager will always be safe to call when the device is in a failed state. For example, in the failure case, `self._imu` will not exist, and any attempt to call it will raise an error `AttributeError: 'LSM6DSOXManager' object has no attribute '_imu'`. While all methods on current device managers are safe to call on failed initialization, there is no enforcement mechanism beyond peer review. We may also want device manager methods to fail in the future, and this proposal will prevent that.
- This pattern requires all device managers to implement the `get_state()` method, which burdens the developer and may lead to inconsistent implementations.

### Pattern 2: Default Manager

We propose to add a failed manager for each type of device. Each failed manager will implement both the protocol for its device and a new `FailedDevice` protocol. Downstream services will be able to check if the device manager is an instance of the `FailedDevice` protocol and handle it accordingly.

#### Example Implementation

`protos/failed_device.py`
```python
class FailedDevice:
    """Protocol for a failed device manager."""
    ...
```

`imu/manager/failed.py`
```py
from protos.imu import IMUProto
from protos.failed_device import FailedDevice
from logging import Logger

class FailedIMUManager(IMUProto, FailedDevice):
    """Manager class for an IMU instance that failed to initialize."""
    def __init__(self, logger: Logger):
        self._log = logger

    def get_gyro_data(self) -> tuple[float, float, float] | None:
        """Get the gyro data from the IMU.

        :return: IMU is not initialized, will always return None.
        :rtype: None
        """
        self._log.warning("IMU is not initialized, gyro data not accessible")
        return None
```


`main.py`
```py
from imu.manager.lsm6dsox import LSM6DSOXManager
from imu.manager.failed import FailedIMUManager

# root try/except block
try:
    try:
        # Initialize the IMU
        imu = LSM6DSOXManager(i2c, address)
    except HardwareInitializationError as e:
        imu = FailedIMUManager(logger)
        logger.error("Failed to initialize IMU", e)

    future_downstream_service(imu)

    # Continue with the rest of the program
```

`future_downstream_service.py`
```py
from protos.imu import IMUProto
from imu.manager.lsm6dsox import LSM6DSOXManager
from imu.manager.failed import FailedIMUManager

def future_downstream_service(imu: IMUProto):
    if isinstance(imu, FailedIMUManager):
        # Handle the case where the IMU is not initialized
        pass

    # Do something with the IMU
```

#### Pros
- Allows downstream services to check the state of a device before attempting to use it.
- It guarantees that device manager methods will always be safe to call when the device is in a failed state. The `Failed...Manager` is a specific protocol implementation that only needs to be written once and can be reused for all devices of the same type.
- This pattern does not require all device managers to implement the `get_state()` method and may lead to inconsistent implementations.

#### Neutral
- This pattern requires PySquared users to return a `FailedDevice` when dealing with a `HardwareInitializationError`. However, this still allows users to handle the error differently if they want to.

#### Cons
- Requires boilerplate `try/except` logic in the device initialization code to instantiate the `Failed...Manager`.
- Relies on `isinstance` checks downstream.

## Decision

TBD
