# Example: Building Frozen Firmware for PROVES Kit

This example walks through building custom CircuitPython firmware with PySquared frozen for a Raspberry Pi Pico (used in PROVES Kit v5).

## Scenario

You want to deploy PySquared to 10 satellites, and you want:
- All libraries built into the firmware (frozen)
- Same library versions on every satellite
- Minimal files on the filesystem
- Maximum available RAM for your application

## Prerequisites

- Linux, macOS, or Windows with WSL
- ARM cross-compiler installed
- ~5GB disk space
- 30-60 minutes for first build

## Step-by-Step Walkthrough

### 1. Install Build Tools

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential git python3 python3-pip gcc-arm-none-eabi

# Verify installation
arm-none-eabi-gcc --version
# Should show: arm-none-eabi-gcc (GNU Arm Embedded Toolchain 10.3-2021.10) 10.3.1
```

### 2. Initial Setup

```bash
cd /path/to/pysquared/firmware
make setup
```

**What this does:**
- Clones CircuitPython 9.2.0 to `circuitpython/`
- Fetches all CircuitPython submodules (~5 minutes)
- Creates symlink: `circuitpython/frozen/pysquared -> ../../../circuitpython-workspaces/flight-software/src/pysquared`
- Shows you what dependencies need to be added

**Expected output:**
```
Checking prerequisites...
All prerequisites satisfied
Cloning CircuitPython 9.2.0...
Fetching CircuitPython submodules...
Setting up frozen modules...
Linking PySquared library to frozen directory...
PySquared linked

Note: Dependencies must be added manually as git submodules
See docs/frozen-modules.md for instructions on adding each dependency

Dependencies to add (from circuitpython-workspaces/flight-software/pyproject.toml):
  - adafruit-circuitpython-ina219
  - adafruit-circuitpython-asyncio
  ...
```

### 3. Add Dependencies

Now add each dependency as a git submodule. We'll start with the standard Adafruit libraries:

```bash
cd circuitpython/frozen

# INA219 - Power monitor
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_INA219
cd Adafruit_CircuitPython_INA219
git checkout 3.4.26
cd ..

# Asyncio - Async I/O support
git submodule add https://github.com/adafruit/adafruit_circuitpython_asyncio
cd adafruit_circuitpython_asyncio
git checkout 1.3.3
cd ..

# DRV2605 - Haptic motor driver
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_DRV2605
cd Adafruit_CircuitPython_DRV2605
git checkout 1.3.4
cd ..

# LIS2MDL - Magnetometer
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_LIS2MDL
cd Adafruit_CircuitPython_LIS2MDL
git checkout 2.1.23
cd ..

# LSM6DS - IMU
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_LSM6DS
cd Adafruit_CircuitPython_LSM6DS
git checkout 4.5.13
cd ..

# MCP9808 - Temperature sensor
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_MCP9808
cd Adafruit_CircuitPython_MCP9808
git checkout 3.3.24
cd ..

# NeoPixel - RGB LED control
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel
cd Adafruit_CircuitPython_NeoPixel
git checkout 6.3.12
cd ..

# Register - Low-level I2C/SPI helper
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_Register
cd Adafruit_CircuitPython_Register
git checkout 1.10.4
cd ..

# RFM - Radio module
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_RFM
cd Adafruit_CircuitPython_RFM
git checkout 1.0.6
cd ..

# TCA9548A - I2C multiplexer (PROVES custom fork)
git submodule add https://github.com/proveskit/Adafruit_CircuitPython_TCA9548A
cd Adafruit_CircuitPython_TCA9548A
git checkout 1.1.0
cd ..

# Ticks - Timing utilities
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_Ticks
cd Adafruit_CircuitPython_Ticks
git checkout 1.1.1
cd ..

# VEML7700 - Light sensor
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_VEML7700
cd Adafruit_CircuitPython_VEML7700
git checkout 2.1.4
cd ..

# Hashlib - Hash functions
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_hashlib
cd Adafruit_CircuitPython_hashlib
git checkout 1.4.19
cd ..

# PROVES SX126X - LoRa radio
git submodule add https://github.com/proveskit/micropySX126X
cd micropySX126X
git checkout 1.0.0
cd ..

# PROVES SX1280 - 2.4GHz radio
git submodule add https://github.com/proveskit/CircuitPython_SX1280
cd CircuitPython_SX1280
git checkout 1.0.4
cd ..
```

**Tip:** You can create a script to automate this. See `add_dependencies.py` for a helper.

### 4. Configure Board

Now tell CircuitPython to include these modules in the firmware:

```bash
cd /path/to/pysquared/firmware/circuitpython/ports/raspberrypi/boards/raspberry_pi_pico
```

Edit `mpconfigboard.mk` and add at the end:

```makefile
# PySquared frozen modules
FROZEN_MPY_DIRS += $(TOP)/frozen/pysquared
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_INA219
FROZEN_MPY_DIRS += $(TOP)/frozen/adafruit_circuitpython_asyncio
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_DRV2605
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_LIS2MDL
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_LSM6DS
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_MCP9808
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_NeoPixel
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Register
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_RFM
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_TCA9548A
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Ticks
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_VEML7700
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_hashlib
FROZEN_MPY_DIRS += $(TOP)/frozen/micropySX126X
FROZEN_MPY_DIRS += $(TOP)/frozen/CircuitPython_SX1280
```

### 5. Build Firmware

```bash
cd /path/to/pysquared/firmware
make firmware BOARD=raspberry_pi_pico
```

**Expected output:**
```
Building firmware for raspberry_pi_pico...
CircuitPython version: 9.2.0
Board: raspberry_pi_pico
...
[lots of compiler output]
...
Firmware built successfully!
Output: /path/to/pysquared/firmware/build/raspberry_pi_pico-frozen-9.2.0.uf2
```

**Build time:** 10-30 minutes on first build. Subsequent builds are much faster (1-5 minutes).

### 6. Flash to Board

1. **Enter bootloader mode:**
   - Connect your PROVES Kit board via USB
   - Double-press the RESET button quickly
   - A USB drive named `RPI-RP2` appears

2. **Copy firmware:**
   ```bash
   cp build/raspberry_pi_pico-frozen-9.2.0.uf2 /media/username/RPI-RP2/
   ```
   (Adjust path for your OS - may be `/Volumes/RPI-RP2` on macOS or `D:\` on Windows)

3. **Board auto-restarts** with new firmware

### 7. Verify Frozen Modules

Connect to serial console:
```bash
screen /dev/ttyACM0  # Linux - adjust device as needed
```

Test in REPL:
```python
>>> import sys
>>> print(sys.implementation)
(name='circuitpython', version=(9, 2, 0))

>>> import pysquared
>>> print(pysquared.__file__)
# Should NOT show a file path - it's built-in (frozen)

>>> from pysquared.hardware.power_monitor import INA219Manager
>>> # Should import without needing files in /lib

>>> import os
>>> os.listdir('/lib')
[]  # Empty! All libraries are frozen
```

### 8. Deploy Your Code

Now you only need to copy your application code:

```python
# main.py
from pysquared import PySquared

# All libraries are already built-in!
satellite = PySquared()
satellite.run()
```

Copy to board:
```bash
cp main.py config.json /media/username/CIRCUITPY/
```

## Results

**Before (standard deployment):**
- CircuitPython firmware: ~1.5 MB
- /lib directory: ~2-3 MB of .mpy files
- Available RAM: ~180 KB (on RP2040)
- Deploy to each board: Copy firmware + copy 50+ library files

**After (frozen modules):**
- CircuitPython firmware: ~2.5 MB (includes libraries)
- /lib directory: 0 bytes
- Available RAM: ~200 KB (20KB more available!)
- Deploy to each board: Copy firmware + copy 2 files (main.py, config.json)

## Troubleshooting

**Problem:** Build fails with "No such file or directory: arm-none-eabi-gcc"

**Solution:** Install ARM toolchain:
```bash
sudo apt install gcc-arm-none-eabi
```

---

**Problem:** Build fails with "git submodule error"

**Solution:** Ensure you're in the right directory and submodule was added:
```bash
cd circuitpython
git submodule status  # Check submodules
make fetch-all-submodules  # Re-fetch if needed
```

---

**Problem:** Import error after flashing: `ImportError: no module named 'adafruit_ina219'`

**Solution:** Check that the module is listed in `mpconfigboard.mk`:
```bash
grep -r "INA219" circuitpython/ports/raspberrypi/boards/raspberry_pi_pico/mpconfigboard.mk
```

---

**Problem:** Firmware is too large (>2MB for RP2040)

**Solution:** Build with size optimization:
```bash
make firmware BOARD=raspberry_pi_pico OPTIMIZATION=-Os
```

Or remove unused libraries from `mpconfigboard.mk`.

## Next Steps

- Build firmware for all your boards
- Test thoroughly on actual hardware
- Create a release with firmware files
- Deploy to your satellite fleet!

## References

- Complete guide: [docs/frozen-modules.md](../docs/frozen-modules.md)
- Quick reference: [QUICKSTART.md](QUICKSTART.md)
- CircuitPython docs: https://docs.circuitpython.org/en/latest/BUILDING.html
