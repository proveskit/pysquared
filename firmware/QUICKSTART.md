# Quick Reference: Building Frozen Firmware

This is a condensed reference for building custom CircuitPython firmware with PySquared libraries frozen. For complete details, see [frozen-modules.md](frozen-modules.md).

## Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install build-essential git python3 python3-pip gcc-arm-none-eabi
```

**macOS:**
```bash
brew install armmbed/formulae/arm-none-eabi-gcc python3 git
```

**Windows:** Use WSL and follow Ubuntu instructions

## Quick Build Guide

### 1. First Time Setup

```bash
cd firmware
make setup
```

This clones CircuitPython 9.2.0, fetches only the submodules needed for RP2040/RP2350 boards (raspberrypi port), and installs the required Python build dependencies in the UV virtual environment (avoiding system Python conflicts on macOS), significantly reducing download size and time.

### 2. Add Dependencies (Manual)

Each dependency from `circuitpython-workspaces/flight-software/pyproject.toml` needs to be added as a git submodule:

```bash
cd circuitpython/frozen

# Example: Add INA219 library
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_INA219
cd Adafruit_CircuitPython_INA219
git checkout 3.4.26  # Match version in pyproject.toml

# Repeat for each dependency...
```

**Dependencies to add:**
- Adafruit_CircuitPython_INA219 (v3.4.26)
- Adafruit_CircuitPython_asyncio (v1.3.3)
- Adafruit_CircuitPython_DRV2605 (v1.3.4)
- Adafruit_CircuitPython_LIS2MDL (v2.1.23)
- Adafruit_CircuitPython_LSM6DS (v4.5.13)
- Adafruit_CircuitPython_MCP9808 (v3.3.24)
- Adafruit_CircuitPython_NeoPixel (v6.3.12)
- Adafruit_CircuitPython_Register (v1.10.4)
- Adafruit_CircuitPython_RFM (v1.0.6)
- Adafruit_CircuitPython_TCA9548A (custom fork)
- Adafruit_CircuitPython_Ticks (v1.1.1)
- Adafruit_CircuitPython_VEML7700 (v2.1.4)
- Adafruit_CircuitPython_hashlib (v1.4.19)
- micropySX126X (v1.0.0)
- CircuitPython_SX1280 (v1.0.4)

Or use the helper script (still needs manual verification):
```bash
cd firmware
./add_dependencies.py --list  # See what would be added
```

### 3. Configure Board

Edit the board configuration to include frozen modules:

```bash
cd circuitpython/ports/raspberrypi/boards/raspberry_pi_pico/
```

Add to `mpconfigboard.mk`:
```makefile
# PySquared frozen modules
FROZEN_MPY_DIRS += $(TOP)/frozen/pysquared
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_INA219
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_LIS2MDL
# ... add all other dependencies
```

### 4. Build Firmware

```bash
cd firmware
make firmware BOARD=raspberry_pi_pico
```

**Important:** Always use `make firmware` from the firmware directory. This ensures the build runs with UV's Python environment where dependencies are installed.

Output: `build/raspberry_pi_pico-frozen-9.2.0.uf2`

### 5. Flash Firmware

1. Put board in bootloader mode (double-press RESET)
2. Copy `build/raspberry_pi_pico-frozen-9.2.0.uf2` to the USB drive that appears
3. Board will reset and boot with frozen modules

### 6. Verify

Connect to serial console and test:
```python
import pysquared
print(pysquared.__file__)  # Should show it's built-in
```

## Common Commands

```bash
# List available boards
make list-boards

# Build for specific board
make firmware BOARD=raspberry_pi_pico

# Build for all boards
make all-boards

# Clean build artifacts
make clean BOARD=raspberry_pi_pico

# Remove everything including CircuitPython
make clean-all

# Show configuration
make info

# Update to different CircuitPython version
make update-circuitpython CIRCUITPYTHON_VERSION=9.1.4
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `arm-none-eabi-gcc: command not found` | Install ARM toolchain (see prerequisites) |
| `No rule to make target` | Check board name with `make list-boards` |
| Firmware too large | Remove unused dependencies or use `OPTIMIZATION=-Os` |
| Import error after flashing | Verify dependency is in `mpconfigboard.mk` |
| Build fails with submodule error | Run `python3 tools/ci_fetch_deps.py raspberrypi` in circuitpython/ |
| Python import errors (cascadetoml, jinja2, etc.) | Run `make install-circuitpython-deps` |
| `externally-managed-environment` error (macOS) | Use `make setup` - now installs in UV virtual environment |

## Advanced

**Build with different CircuitPython version:**
```bash
make setup CIRCUITPYTHON_VERSION=9.1.4
```

**Optimize for size:**
```bash
make firmware BOARD=raspberry_pi_pico OPTIMIZATION=-Os
```

**Verbose build:**
```bash
make firmware BOARD=raspberry_pi_pico V=1
```

## What Gets Frozen

When you build firmware:
- ✅ PySquared library (`pysquared` package)
- ✅ All dependencies from pyproject.toml
- ✅ No need for `/lib` directory on the board
- ❌ User code (main.py, config.json) still goes on filesystem

## Updating

To update frozen modules:
1. Update library source code
2. Rebuild firmware: `make firmware BOARD=<board>`
3. Flash new firmware to all boards

**Note:** You cannot update frozen modules without reflashing firmware.

## Support

- Full guide: [frozen-modules.md](frozen-modules.md)
- CircuitPython docs: https://docs.circuitpython.org/
- Issues: https://github.com/proveskit/pysquared/issues
