# Board Configuration Examples for PROVES Kit

This directory contains example board configuration files for PROVES Kit hardware.

These configurations show how to add PySquared libraries as frozen modules to CircuitPython firmware for different PROVES board versions.

## Usage

After running `make setup`, these configurations need to be integrated into the CircuitPython source tree:

### Option 1: Create New Board Definitions

If you want to create new board variants specifically for PROVES Kit:

```bash
# Copy board config to CircuitPython source
cp boards/proves_rp2040_v5/mpconfigboard.mk \
   circuitpython/ports/raspberrypi/boards/proves_rp2040_v5/

cp boards/proves_rp2040_v5/mpconfigboard.h \
   circuitpython/ports/raspberrypi/boards/proves_rp2040_v5/

cp boards/proves_rp2040_v5/pins.c \
   circuitpython/ports/raspberrypi/boards/proves_rp2040_v5/
```

### Option 2: Modify Existing Board Definitions

If you want to add frozen modules to existing Raspberry Pi Pico boards:

```bash
# Edit the mpconfigboard.mk for your board
# For example, for Raspberry Pi Pico:
cd circuitpython/ports/raspberrypi/boards/raspberry_pi_pico/

# Add this to the end of mpconfigboard.mk:
cat >> mpconfigboard.mk << 'EOF'

# PySquared frozen modules
FROZEN_MPY_DIRS += $(TOP)/frozen/pysquared
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_INA219
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_LIS2MDL
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_LSM6DS
# ... add all other dependencies
EOF
```

## Board Files

Each board directory should contain:

- **mpconfigboard.h** - C header with board-specific pin definitions and features
- **mpconfigboard.mk** - Makefile with board configuration including frozen modules
- **pins.c** - Pin mapping for CircuitPython
- **board.c** (optional) - Board-specific initialization code

## Example: Adding Frozen Modules to mpconfigboard.mk

```makefile
# Base board configuration
USB_VID = 0x2E8A
USB_PID = 0x0003
USB_PRODUCT = "PROVES Kit v5"
USB_MANUFACTURER = "PROVES"

CHIP_VARIANT = RP2040
CHIP_FAMILY = rp2

EXTERNAL_FLASH_DEVICES = "W25Q16JVxQ"

# Add PySquared and all dependencies as frozen modules
FROZEN_MPY_DIRS += $(TOP)/frozen/pysquared

# Adafruit CircuitPython Libraries
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Ina219
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_asyncio
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_DRV2605
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Lis2mdl
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_LSM6DS
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Mcp9808
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Register
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_RFM
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_TCA9548A
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Ticks
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Veml7700
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Hashlib

# PROVES CircuitPython Libraries
FROZEN_MPY_DIRS += $(TOP)/frozen/micropySX126X
FROZEN_MPY_DIRS += $(TOP)/frozen/CircuitPython_SX1280
```

## PROVES Kit Board Variants

The PROVES Kit has multiple hardware versions:

| Board | Chip | Flash | Description |
|-------|------|-------|-------------|
| v4 | RP2040 | 2MB | Early version |
| v5 | RP2040 | 2MB | Current RP2040 version |
| v5a | RP2350 | 4MB | New RP2350 variant A |
| v5b | RP2350 | 4MB | New RP2350 variant B |

Each may need slightly different configurations for:
- Pin assignments
- Flash chip specifications
- Peripheral configurations

## Building with Custom Board

After setting up board files:

```bash
# Build for custom PROVES board
make firmware BOARD=proves_rp2040_v5

# Or modify an existing board
make firmware BOARD=raspberry_pi_pico
```

## References

- [CircuitPython Board Porting Guide](https://learn.adafruit.com/how-to-add-a-new-board-to-circuitpython)
- [RP2040 Board Examples](https://github.com/adafruit/circuitpython/tree/main/ports/raspberrypi/boards)
- [PySquared Dependencies](../../circuitpython-workspaces/flight-software/pyproject.toml)
