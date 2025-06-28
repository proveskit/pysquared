# Non-Volatile Flag

### flag Module
This module provides the `Flag` class for managing boolean flags stored in non-volatile memory (NVM) on CircuitPython devices.

#### Imports
```py title="flag.py"
import microcontroller
```

### Flag Class
Manages boolean flags stored in non-volatile memory.

#### Attributes
- **_index** (int): The index of the flag (byte) in the NVM datastore.
- **_bit** (int): The bit index within the byte.
- **_datastore** (microcontroller.nvm.ByteArray): The NVM datastore.
- **_bit_mask** (int): Bitmask for the flag's bit position.

### Initialization of Flag Instance

#### Arguments
- **index** (int): The index of the flag (byte) in the datastore.
- **bit_index** (int): The index of the bit within the byte.

```py title="flag.py"
def __init__(self, index: int, bit_index: int) -> None:
    self._index = index
    self._bit = bit_index

    if microcontroller.nvm is None:
        raise ValueError("nvm is not available")

    self._datastore = microcontroller.nvm  # Array of bytes (Non-volatile Memory)
    self._bit_mask = 1 << bit_index  # Creating bitmask with bit position
    # Ex. bit = 3 -> 1 << 3 = 00001000
```

### Getting the Flag Value

#### Returns
- **bool**: The current value of the flag.

```py title="flag.py"
def get(self) -> bool:
    return bool(self._datastore[self._index] & self._bit_mask)
```

### Setting or Clearing the Flag

#### Arguments
- **value** (bool): If True, sets the flag; if False, clears the flag.

```py title="flag.py"
def toggle(self, value: bool) -> None:
    if value:
        # If true, perform OR on specific byte and bitmask to set bit to 1
        self._datastore[self._index] |= self._bit_mask
    else:
        # If false, perform AND on specific byte and inverted bitmask to set bit to 0
        self._datastore[self._index] &= ~self._bit_mask
```
