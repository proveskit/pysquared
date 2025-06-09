# Non-Volatile Counter

### counter Module
This module provides the `Counter` class for managing 8-bit counters stored in non-volatile memory (NVM) on CircuitPython devices.

#### Imports
```py title="counter.py"
import microcontroller
```

### Counter Class
Manages 8-bit counters stored in non-volatile memory.

#### Attributes
- **_index** (int): The index of the counter in the NVM datastore.
- **_datastore** (microcontroller.nvm.ByteArray): The non-volatile memory datastore where the counter is stored.

### Initialization of Counter Instance

#### Arguments
- **index** (int): The index of the counter in the datastore.

```py title="counter.py"
def __init__(self, index: int) -> None:
    self._index = index

    if microcontroller.nvm is None:
        raise ValueError("nvm is not available")

    self._datastore = microcontroller.nvm
```

### Getting the Counter Value

#### Returns
- **int**: The current value of the counter.

```py title="counter.py"
def get(self) -> int:
    return self._datastore[self._index]
```

### Incrementing the Counter

Increments the counter by one, with rollover at 8 bits (0-255).

```py title="counter.py"
def increment(self) -> None:
    value: int = (self.get() + 1) & 0xFF  # 8-bit counter with rollover
    self._datastore[self._index] = value
```
