# Building Custom CircuitPython Firmware with Frozen Modules

## Overview

**Frozen modules** are Python libraries that are compiled directly into the CircuitPython firmware binary, rather than being stored as separate files on the CIRCUITPY filesystem. This approach provides several benefits:

- **RAM Savings**: Frozen modules execute directly from flash memory, freeing up precious RAM for your application code
- **Flash Efficiency**: Compiled frozen modules take less space than `.mpy` files on the filesystem
- **Simplified Deployment**: Single firmware file contains everything - no need to copy libraries to each board
- **Faster Startup**: Pre-compiled modules load faster than filesystem-based libraries
- **Version Consistency**: Ensures all boards run exactly the same library versions

This is particularly valuable for resource-constrained boards like SAMD21 or when deploying to many satellites.

## When to Use Frozen Modules

**Use frozen modules when:**
- You're deploying to many boards and want consistency
- Your board is RAM-constrained (e.g., SAMD21 non-Express boards)
- You want to prevent accidental library modifications on the board
- You need faster startup times
- You want to simplify your deployment process

**Use filesystem libraries when:**
- You need to update libraries without reflashing firmware
- You're actively developing and testing new library versions
- You want flexibility to mix and match library versions
- Your board has plenty of RAM and flash

## Prerequisites

Building custom CircuitPython firmware requires:

1. **Linux, macOS, or Windows with WSL**: The build system requires a Unix-like environment
2. **Build Tools**: 
   - `gcc-arm-none-eabi` (ARM cross-compiler)
   - `git` (version control)
   - `python3` and `pip` (for build scripts)
   - `make` (build system)
3. **Disk Space**: ~5GB for CircuitPython source and build artifacts
4. **Time**: Initial build takes 10-30 minutes depending on your system

## Build Process Overview

The frozen module build process involves:

1. **Clone CircuitPython Source**: Get the CircuitPython repository and all submodules
2. **Add PySquared Dependencies**: Configure which libraries to freeze into firmware
3. **Configure Board**: Specify board type and frozen module directories
4. **Build Firmware**: Compile CircuitPython with frozen modules
5. **Flash Firmware**: Upload the custom firmware to your board

## Directory Structure

We recommend creating a `firmware/` directory in this repository to contain all firmware-related build artifacts:

```
pysquared/
├── firmware/                           # Frozen module build directory (new)
│   ├── circuitpython/                 # CircuitPython source (git submodule)
│   ├── frozen/                        # Directory for libraries to freeze
│   │   ├── pysquared/                 # PySquared library (symlink or copy)
│   │   └── adafruit_circuitpython_*/  # Adafruit dependencies (git submodules)
│   ├── boards/                        # Custom board configurations
│   │   ├── proves_rp2040_v4/
│   │   ├── proves_rp2040_v5/
│   │   ├── proves_rp2350_v5a/
│   │   └── proves_rp2350_v5b/
│   ├── Makefile                       # Build automation
│   ├── build-firmware.sh              # Build script
│   └── README.md                      # Firmware-specific documentation
├── circuitpython-workspaces/          # Existing PySquared source
└── docs/                              # Documentation
```

## Step-by-Step Build Instructions

### 1. Set Up Build Environment

#### On Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install build-essential git python3 python3-pip gcc-arm-none-eabi
```

#### On macOS:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ARM toolchain
brew install armmbed/formulae/arm-none-eabi-gcc
brew install python3 git
```

#### On Windows (WSL):
```bash
# First install WSL and Ubuntu from Microsoft Store, then:
sudo apt update
sudo apt install build-essential git python3 python3-pip gcc-arm-none-eabi
```

### 2. Clone CircuitPython Source

Navigate to the `firmware/` directory and clone CircuitPython:

```bash
cd firmware/
git clone https://github.com/adafruit/circuitpython.git
cd circuitpython
git checkout <stable-version-tag>  # e.g., 9.0.5
python3 tools/ci_fetch_deps.py raspberrypi
# Return to firmware directory and use UV to install build dependencies
cd ..
# Ensure UV is available (installed by root Makefile)
cd .. && make uv && cd firmware
# Install in UV virtual environment
../tools/uv-0.8.14/uv pip install -q -r circuitpython/requirements-dev.txt
```

**Note**: This fetches only submodules needed for RP2040/RP2350 (raspberrypi port), significantly reducing download size and time. To fetch all submodules (for other boards), use `make fetch-all-submodules` instead.

**Important**: 
- Always use a tagged stable release, not the main branch, to ensure reproducible builds.
- The `requirements-dev.txt` install provides Python tools needed for the build (cascadetoml, jinja2, typer, etc.).
- Using `make setup` (recommended) automatically installs dependencies in the UV virtual environment, avoiding system Python conflicts.

### 3. Add Libraries to Freeze

You have two options for adding libraries:

#### Option A: Add as Git Submodules (Recommended for Dependencies)

For each Adafruit library dependency in `circuitpython-workspaces/flight-software/pyproject.toml`:

```bash
cd firmware/circuitpython/frozen
git submodule add https://github.com/adafruit/Adafruit_CircuitPython_INA219
cd Adafruit_CircuitPython_INA219
git checkout <version-tag>  # Match version in pyproject.toml
```

#### Option B: Symlink PySquared Library

For the PySquared library itself:

```bash
cd firmware/circuitpython/frozen
ln -s ../../../circuitpython-workspaces/flight-software/src/pysquared pysquared
```

This keeps the source in one place and avoids duplication.

### 4. Configure Board

Create or modify the board configuration in `ports/raspberrypi/boards/<BOARD_NAME>/mpconfigboard.mk`:

```makefile
# Add PySquared and dependencies to frozen modules
FROZEN_MPY_DIRS += $(TOP)/frozen/pysquared
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_INA219
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_LIS2MDL
# ... add all other dependencies
```

### 5. Build Firmware

**Recommended:** Use the firmware Makefile which ensures the correct Python environment:

```bash
cd firmware
make firmware BOARD=raspberry_pi_pico
```

**Manual (advanced):** If building directly in CircuitPython source:

```bash
cd firmware/circuitpython/ports/raspberrypi
# Use UV to run make with the correct Python environment
../../tools/uv-0.8.14/uv run --no-project make BOARD=<board_name>
```

For PROVES Kit boards (or use equivalent Raspberry Pi Pico boards):
- `raspberry_pi_pico` (for v4, v5)
- `raspberry_pi_pico_w` (with WiFi)
- Custom PROVES board definitions (once configured)

The build will create a `.uf2` file in `build-<BOARD_NAME>/firmware.uf2`.

### 6. Flash Firmware

1. Put your board in bootloader mode (double-press RESET button)
2. A USB drive named `RPI-RP2` or similar will appear
3. Copy the `firmware.uf2` file to this drive
4. The board will automatically reset and boot with the new firmware

## Verifying Frozen Modules

After flashing, connect to the board's serial console and run:

```python
import sys
print(sys.modules)
```

Frozen modules will be listed and can be imported directly without being in `/lib`.

Test that PySquared is frozen:

```python
import pysquared
print(pysquared.__file__)  # Should show it's built-in, not from filesystem
```

## Automating the Build

To make builds easier, create a `firmware/Makefile`:

```makefile
# Version pins
CIRCUITPYTHON_VERSION ?= 9.0.5
BOARD ?= proves_rp2040_v5

.PHONY: all
all: firmware

.PHONY: setup
setup:
	git clone https://github.com/adafruit/circuitpython.git || true
	cd circuitpython && git checkout $(CIRCUITPYTHON_VERSION)
	cd circuitpython && python3 tools/ci_fetch_deps.py raspberrypi
	# Use UV for installing build dependencies (avoids system Python conflicts)
	cd .. && make uv && cd firmware
	../tools/uv-0.8.14/uv pip install -q -r circuitpython/requirements-dev.txt
	$(MAKE) add-dependencies

.PHONY: add-dependencies
add-dependencies:
	# Add each dependency from pyproject.toml as a submodule
	# This would parse the pyproject.toml and add submodules automatically

.PHONY: firmware
firmware:
	cd circuitpython/ports/raspberrypi && make BOARD=$(BOARD)
	cp circuitpython/ports/raspberrypi/build-$(BOARD)/firmware.uf2 ./$(BOARD)-frozen-$(CIRCUITPYTHON_VERSION).uf2

.PHONY: clean
clean:
	cd circuitpython/ports/raspberrypi && make BOARD=$(BOARD) clean
```

Then build with:
```bash
make BOARD=proves_rp2040_v5 firmware
```

## Updating Frozen Modules

When you update PySquared or dependencies:

1. Update the library source code
2. Rebuild the firmware: `make BOARD=<board> firmware`
3. Flash the new firmware to all boards

There's no way to update frozen modules without rebuilding and reflashing the entire firmware.

## Troubleshooting

### Build Fails with "arm-none-eabi-gcc: command not found"
Install the ARM toolchain for your platform (see prerequisites above).

### Build Fails with Missing Submodules
For RP2040/RP2350 builds, run `python3 tools/ci_fetch_deps.py raspberrypi` in the circuitpython directory. For all ports, use `make fetch-all-submodules` instead.

### Build Fails with Python Import Errors (cascadetoml, jinja2, typer, etc.)
First, ensure dependencies are installed: `make install-circuitpython-deps`

If the error persists during build, ensure you're using the Makefile to build: `make firmware BOARD=<board>`. This runs the build with UV's Python environment. Do NOT run `make` directly in the CircuitPython ports directory, as it won't have access to the installed packages.

### "externally-managed-environment" Error on macOS
This occurs when trying to install packages system-wide. The Makefile now uses UV to install in a virtual environment. If you see this error, ensure you're using `make setup` or `make install-circuitpython-deps` rather than manual pip commands.

### Firmware File is Too Large
- Remove unused frozen modules from `mpconfigboard.mk`
- Use `FROZEN_MPY_DIRS` instead of `FROZEN_PY_DIRS` (mpy is more compact)
- Consider building with optimizations: `make BOARD=<board> OPTIMIZATION=-O2`

### Board Won't Boot After Flashing
- Verify you built for the correct board
- Try re-flashing the official CircuitPython firmware first
- Check the build log for errors

### Module Not Found After Freezing
- Verify the module directory is listed in `FROZEN_MPY_DIRS`
- Check that the module has an `__init__.py`
- Rebuild with `make clean` first to ensure fresh build

## CI/CD Integration

For automated builds in GitHub Actions, you can create a workflow that:

1. Sets up the ARM toolchain
2. Clones CircuitPython at a pinned version
3. Adds dependencies as submodules
4. Builds firmware for all PROVES boards
5. Uploads firmware files as release artifacts

Example `.github/workflows/build-firmware.yaml`:

```yaml
name: Build Frozen Firmware

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-firmware:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        board: [proves_rp2040_v4, proves_rp2040_v5, proves_rp2350_v5a, proves_rp2350_v5b]
    
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Install ARM toolchain
        run: |
          sudo apt update
          sudo apt install -y gcc-arm-none-eabi build-essential git python3 python3-pip
      
      - name: Build firmware
        run: |
          cd firmware
          make setup CIRCUITPYTHON_VERSION=9.0.5
          make firmware BOARD=${{ matrix.board }}
      
      - name: Upload firmware
        uses: actions/upload-artifact@v4
        with:
          name: firmware-${{ matrix.board }}
          path: firmware/${{ matrix.board }}-frozen-*.uf2
```

## Best Practices

1. **Pin Versions**: Always use specific version tags for CircuitPython and libraries
2. **Document Dependencies**: Keep a clear record of what's frozen and why
3. **Test Thoroughly**: Test firmware on actual hardware before deploying to all boards
4. **Backup**: Keep copies of working firmware files for rollback
5. **Version Firmware**: Include version info in the firmware filename
6. **Automate**: Use Makefiles or scripts to make builds reproducible
7. **CI/CD**: Automate firmware builds for releases

## References

- [CircuitPython Building Documentation](https://docs.circuitpython.org/en/latest/BUILDING.html)
- [Adafruit Guide: Adding Frozen Modules](https://learn.adafruit.com/building-circuitpython/adding-frozen-modules)
- [CircuitPython Frozen Libraries Overview](https://learn.adafruit.com/welcome-to-circuitpython/library-file-types-and-frozen-libraries)
- [CircuitPython GitHub Repository](https://github.com/adafruit/circuitpython)

## Support

If you encounter issues building firmware:

1. Check the [CircuitPython Discord](https://adafru.it/discord) #help-with-circuitpython channel
2. Open an issue in this repository with your build log
3. Review the CircuitPython documentation for your specific board
