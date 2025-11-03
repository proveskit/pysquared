# PySquared Frozen Firmware Builder

This directory contains the infrastructure for building custom CircuitPython firmware with PySquared libraries frozen (compiled into the firmware binary).

## Quick Start

See the main [Frozen Modules Documentation](../docs/frozen-modules.md) for complete instructions.

### Prerequisites

1. Linux, macOS, or Windows with WSL
2. ARM cross-compiler: `gcc-arm-none-eabi`
3. Build tools: `git`, `make`, `python3`

Install on Ubuntu/Debian:
```bash
sudo apt update
sudo apt install build-essential git python3 python3-pip gcc-arm-none-eabi
```

### Build Firmware

1. **Initial setup** (only needed once):
   ```bash
   make setup
   ```
   This clones CircuitPython and sets up dependencies.

2. **Build for a specific board**:
   ```bash
   make firmware BOARD=proves_rp2040_v5
   ```

3. **Flash firmware** to your board:
   - Put board in bootloader mode (double-press RESET)
   - Copy `build/<BOARD>-frozen-<VERSION>.uf2` to the USB drive that appears

## Supported Boards

- `proves_rp2040_v4` - PROVES Kit v4 (RP2040)
- `proves_rp2040_v5` - PROVES Kit v5 (RP2040)
- `proves_rp2350_v5a` - PROVES Kit v5a (RP2350)
- `proves_rp2350_v5b` - PROVES Kit v5b (RP2350)

## What Gets Frozen

All dependencies from `circuitpython-workspaces/flight-software/pyproject.toml` are frozen into the firmware:

- `pysquared` library (the flight software itself)
- `adafruit-circuitpython-ina219`
- `adafruit-circuitpython-asyncio`
- `adafruit-circuitpython-drv2605`
- `adafruit-circuitpython-lis2mdl`
- `adafruit-circuitpython-lsm6ds`
- `adafruit-circuitpython-mcp9808`
- `adafruit-circuitpython-neopixel`
- `adafruit-circuitpython-register`
- `adafruit-circuitpython-rfm`
- `adafruit-circuitpython-tca9548a`
- `adafruit-circuitpython-ticks`
- `adafruit-circuitpython-veml7700`
- `adafruit-circuitpython-hashlib`
- `proves-circuitpython-sx126`
- `proves-circuitpython-sx1280`

## Makefile Targets

- `make setup` - Clone CircuitPython and dependencies (first-time setup)
- `make firmware BOARD=<board>` - Build firmware for specified board
- `make all-boards` - Build firmware for all PROVES boards
- `make clean` - Clean build artifacts for a board
- `make clean-all` - Remove all build artifacts and CircuitPython source
- `make help` - Show available targets

## Configuration

Edit `Makefile` to change:

- `CIRCUITPYTHON_VERSION` - Version of CircuitPython to build (default: 9.2.0)
- Board-specific frozen modules in board configuration files

## Directory Structure

After running `make setup`:

```
firmware/
├── circuitpython/          # CircuitPython source (git clone)
│   ├── frozen/            # Libraries to freeze
│   │   ├── pysquared/    # Symlink to PySquared source
│   │   └── ...           # Adafruit dependencies (git submodules)
│   └── ports/
│       └── raspberrypi/  # RP2040/RP2350 builds
├── boards/                # Custom board configurations
├── build/                 # Output firmware files
├── Makefile              # Build automation
└── README.md             # This file
```

## Troubleshooting

### "arm-none-eabi-gcc: command not found"
Install the ARM toolchain (see Prerequisites above).

### "No rule to make target 'build-<BOARD>'"
Check that BOARD name is correct. Use `make list-boards` to see available boards.

### Firmware too large
Remove unused dependencies or optimize build:
```bash
make firmware BOARD=<board> OPTIMIZATION=-Os
```

### Import errors after flashing
Verify all dependencies are in the frozen modules list. Check `mpconfigboard.mk` for your board.

## Advanced Usage

### Building Custom CircuitPython Version

```bash
make setup CIRCUITPYTHON_VERSION=9.1.4
make firmware BOARD=proves_rp2040_v5
```

### Adding Custom Frozen Modules

1. Add the library to `circuitpython/frozen/`
2. Update `boards/<BOARD>/mpconfigboard.mk`
3. Rebuild: `make firmware BOARD=<BOARD>`

### Build Options

```bash
# Optimize for size
make firmware BOARD=<board> OPTIMIZATION=-Os

# Enable debug symbols
make firmware BOARD=<board> DEBUG=1

# Verbose build output
make firmware BOARD=<board> V=1
```

## CI/CD

See `.github/workflows/build-firmware.yaml` for automated builds on GitHub Actions.

## More Information

- [Complete Frozen Modules Guide](../docs/frozen-modules.md)
- [CircuitPython Build Documentation](https://docs.circuitpython.org/en/latest/BUILDING.html)
- [PySquared Documentation](https://proveskit.github.io/pysquared/)
