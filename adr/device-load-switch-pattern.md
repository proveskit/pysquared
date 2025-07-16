# Device Load Switch Pattern

## Status

Proposed, partial implementation.

## Context

This ADR proposes a pattern for integrating power state control into device managers. For example, if a sensor (or group of sensors) can be turned on or off by an hardware `enable` pin we want to provide a consistent way for that to happen within the device manager itself. By allowing the device manager to control its own power state, the manager object does not need to rely on outside services to determine whether or not it the devices it is overseeing are currently powered on or off.

### Prior Implementation

Previously in v1.0.0 of the PySquared codebase devices would be directly turned on or off by calling the `enable` pin in runtime, with activation state being stored in a global `cubesat.hardware` dictionary that had the names of sensors as the key and a True / False `Boolean` value for determining whether not not a sensor of availible at any given time. Before making calls to a hardware device, the runtime would first have to check the `cubesat.hardware` dictionary for whether or not the sensor was availible at that time.

```py
    # Example From Yearling 1
    self.hardware = {
                    'IMU':    False,
                    'Radio1': False,
                    'SDcard': False,
                    'WDT':    False,
                    'USB':    False,
                    'PWR':    False,
                    'Face0':  False,
                    'Face1':  False,
                    'Face2':  False,
                    'Face3':  False,
                    'Face4':  False,
                    'Face5':  False,
                    } 
    ...
    @property
    def current_draw(self):
        """
        current draw from batteries
        NOT accurate if powered via USB
        """
        if self.hardware['PWR']:
            idraw=0
            try:
                for _ in range(50): # average 50 readings
                    idraw+=self.pwr.read()[1]
                return (idraw/50)*1000 # mA
            except Exception as e:
                print(f'[WARNING][PWR Monitor]{e}')
        else:
            print('[WARNING] Power monitor initialization issue')
```

This worked *alright* but had a significant drawback in that it would seriously clutter the runtime with repetative checks to see whether or not hardware devices were currently activated before making any function calls. Additionally, by requiring the developer to manually implement checks in the `main` sequence on every function call there is a significant risk that a activation check is forgotten and the runtime attempts to call a deactivated sensor. This can easily lead to unhandled exceptions or software hangs that would crash the flight software. 

### Current State
Currently, enabling and disabling devices must be manually handled in runtime. There was an initial attempt at solving this issue in [#267 Vibecoded Load Switch Manager](https://github.com/proveskit/pysquared/pull/267). That PR created a unique load switch manager component that would bundle all of the enable pins into a single manager object that could be called from the device managers as a service. This approach was abandoned as it creates some logical confusion and still has the issue of the device managers being unable to determine their own state without an external service.

## Proposal

### A Load Switch Proto Inheritied by Device Managers
We propose adding a `LoadSwitchManager` proto that can be inherited by individual device managers.