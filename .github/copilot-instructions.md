# PySquared Copilot Instructions

## Repository Overview

**PySquared** is a CircuitPython-based CubeSat flight software library with flight heritage. It provides robust, modular components for spacecraft control, telemetry, configuration, and hardware management designed for microcontroller resource constraints.

### Key Characteristics
- **Size**: ~142 Python files, ~1,600 lines of code
- **Languages**: Python (CircuitPython 3.4 subset + type hints)
- **Primary Framework**: CircuitPython for embedded systems
- **Test Framework**: pytest with coverage, pyright for type checking
- **Build System**: Makefile + uv (Python package manager)
- **Documentation**: MkDocs with Material theme
- **License**: MIT

### Dual Workspace Architecture
This repository uses a **unique dual workspace structure** to support both CircuitPython (microcontroller) and CPython (testing/tools):

1. **`circuitpython-workspaces/`**: Code that runs on CircuitPython microcontrollers
   - `flight-software/`: Main PySquared library (`pysquared` package)
   - `ground-station/`: Ground station software
   - Uses CircuitPython typeshed stubs for accurate type checking

2. **`cpython-workspaces/`**: Code that runs on standard Python
   - `flight-software-unit-tests/`: pytest test suite
   - `flight-software-mocks/`: Mock hardware for testing
   - Uses standard Python type hints

**CRITICAL**: Always respect workspace boundaries. CircuitPython code cannot use CPython-only libraries (e.g., `pathlib`, full `typing` module) and vice versa.

## Build & Validation Commands

### Initial Setup (ALWAYS run first)
```bash
make
```
This command:
- Downloads and installs `uv` (v0.8.14) to `tools/uv-0.8.14/`
- Creates `.venv/` virtual environment
- Installs all dependencies from `pyproject.toml`
- Installs CircuitPython typeshed stubs to `circuitpython-workspaces/typeshed/`
- Installs pre-commit hooks

**Expected time**: 30-60 seconds (first run)

### Linting & Formatting
```bash
make fmt
```
- Runs `pre-commit run --all-files`
- Uses ruff for linting/formatting (follows Black style + isort)
- Includes custom checks: prevents `# type: ignore`, checks spelling, validates JSON/YAML
- **ALWAYS run before committing code**
- Auto-fixes most issues; manual fixes required for some errors

**Expected time**: 10-20 seconds

### Type Checking
```bash
make typecheck
```
- Runs `pyright` on both workspaces separately
- CircuitPython workspace: uses custom typeshed stubs
- CPython workspace: uses standard library type hints
- **Zero tolerance** for `# type: ignore` in flight software (except for documented upstream bugs with PR links)

**Expected time**: 15-30 seconds

### Testing
```bash
make test
```
- Runs pytest on `cpython-workspaces/flight-software-unit-tests/src`
- Generates coverage reports in `.coverage-reports/`
- **Target**: 100% code coverage
- Uses `coverage` with branch coverage enabled

**Expected time**: 20-40 seconds

### Documentation (Local Preview)
```bash
make docs
```
- Serves documentation locally at `http://localhost:8000`
- Uses MkDocs with Material theme
- Auto-reloads on file changes

### Cleaning Build Artifacts
```bash
make clean
```
- Removes all git-ignored files (`.venv`, `.coverage-reports`, `tools/`, etc.)
- Use when environment is corrupted or dependencies need fresh install

## CI/CD Pipeline (GitHub Actions)

The repository runs three parallel CI jobs on all PRs and pushes to `main`:

1. **Lint** (`.github/workflows/ci.yaml`):
   - Runs `make fmt`
   - **Failure**: Code style violations, missing trailing newlines, `# type: ignore` in flight-software

2. **Typecheck**:
   - Runs `make typecheck`
   - **Failure**: Type errors in either workspace, missing type hints

3. **Test**:
   - Runs `TEST_SELECT=ALL make test`
   - Uploads coverage to SonarQube
   - **Failure**: Test failures, coverage regression

**All three must pass** before merging. Always run these commands locally before pushing.

## Project Layout & Architecture

### Root Directory Files
```
.devcontainer/           # Dev container configuration for VS Code
.github/workflows/       # CI/CD workflows (ci.yaml, docs.yaml)
.vscode/                 # VS Code workspace settings
circuitpython-workspaces/  # CircuitPython code
cpython-workspaces/      # CPython code (tests, mocks)
docs/                    # MkDocs documentation
Makefile                 # Build commands
pyproject.toml           # Root workspace configuration
pysquared.code-workspace # VS Code workspace file (ALWAYS use this)
.pre-commit-config.yaml  # Pre-commit hook definitions
mkdocs.yaml              # Documentation build configuration
uv.lock                  # Locked dependencies
```

### Flight Software Structure (`circuitpython-workspaces/flight-software/src/pysquared/`)
```
pysquared/
├── __init__.py
├── beacon.py            # Beacon transmission logic
├── binary_encoder.py    # Data encoding utilities
├── cdh.py               # Command & Data Handling
├── config/              # Configuration management (Config, RadioConfig)
│   ├── config.py        # Main config class (loads from JSON)
│   └── radio_config.py
├── detumble.py          # Attitude control algorithms
├── file_validation/     # File integrity checking
├── hardware/            # Hardware drivers (organized by sensor type)
│   ├── burnwire/        # Deployment mechanism drivers
│   ├── imu/             # Inertial Measurement Unit (LSM6DS)
│   ├── light_sensor/    # Light sensors (VEML7700)
│   ├── load_switch/     # Power switching
│   ├── magnetometer/    # Magnetometers (LIS2MDL)
│   ├── power_monitor/   # Power monitoring (INA219)
│   ├── radio/           # Radio drivers (RFM, SX126x, SX1280)
│   ├── sd_card/         # SD card management
│   └── temperature_sensor/  # Temperature sensors (MCP9808)
├── logger.py            # JSON-structured logging (Loguru-style API)
├── nvm/                 # Non-volatile memory (Counter, Flag classes)
├── power_health.py      # Power monitoring and battery management
├── protos/              # Protocol definitions (base classes with `...`)
├── rtc/                 # Real-time clock management
├── sensor_reading/      # Sensor data structures (SI units required)
├── sleep_helper.py      # Safe sleep with watchdog petting
└── watchdog.py          # Watchdog timer management
```

**Hardware Manager Pattern**: Each hardware type has a `manager/` subdirectory containing driver implementations that implement protocols from `protos/`.

### Test Structure (`cpython-workspaces/flight-software-unit-tests/src/unit-tests/`)
- Mirrors flight software structure
- Uses pytest fixtures extensively
- Mocks hardware via `flight-software-mocks` workspace

### Configuration Files
- **pyproject.toml**: Python project metadata, tool configs (ruff, pytest, coverage, interrogate)
- **pyrightconfig.json**: Type checker configuration (separate files for each workspace)
- **.pre-commit-config.yaml**: Pre-commit hooks (ruff, codespell, custom validators)
- **mkdocs.yaml**: Documentation site structure

## Critical Development Guidelines

### Code Style & Quality
1. **Always use relative imports** in flight software:
   ```python
   from .sensors.temperature import TemperatureSensor  # ✓ Correct
   from pysquared.sensors.temperature import ...       # ✗ Wrong
   ```

2. **Sensor readings must be in SI units** with timestamps (see design-guide.md for full table)

3. **Error handling**: Use try/except blocks, log with `logger.error()`, return default values on sensor failures

4. **Avoid `typing` module in CircuitPython code** (not supported):
   ```python
   # ✗ Don't do this in circuitpython-workspaces
   from typing import List, Optional

   # ✓ Use this pattern instead
   try:
       from typing import List, Optional
   except ImportError:
       pass
   ```

5. **Configuration**: All config loads from JSON files (`config.json`, `jokes.json`)

6. **Documentation**: All modules, classes, and functions require docstrings (enforced by interrogate)

### Testing Requirements
- 100% code coverage target
- Use mocks from `flight-software-mocks` workspace
- Test files mirror source structure: `test_<module>.py`
- Use pytest fixtures for setup/teardown

### VS Code Workspace Setup
**ALWAYS open `pysquared.code-workspace`** in VS Code, not the raw folder. This provides:
- Correct type hints for both CircuitPython and CPython code
- Prevents false positives from mixing workspace type systems
- Proper pyright configuration per workspace

See contributing.md for detailed workspace setup instructions.

## Common Issues & Workarounds

### Network Dependency Installation Failures
If `make` fails to download `uv` due to network issues, the build will fail. This is expected in restricted environments. The Makefile downloads `uv` from `https://astral.sh/uv/0.8.14/install.sh`.

### Type Ignore Exceptions
Only allowed in flight software with upstream bug links:
```python
variable = function()  # type: ignore  # PR https://github.com/org/repo/pull/123
```
Excluded files (legacy): `beacon.py`, `logger.py`, `rtc/manager/microcontroller.py`, `hardware/sd_card/manager/sd_card.py`

### CircuitPython Compatibility
- Python 3.4 syntax + type hints only
- No `pathlib`, `asyncio` (except Adafruit's CircuitPython version), or most stdlib modules
- See design-guide.md for full list of differences

### Pre-commit Hook Failures
If pre-commit hooks fail during commit:
```bash
make fmt  # Auto-fixes most issues
# Review remaining errors, fix manually, then commit again
```

## Validation Checklist

Before submitting a PR, ALWAYS run:
```bash
make fmt        # Fix formatting
make typecheck  # Verify types
make test       # Run tests
```

All three must pass with zero errors. Check the output carefully:
- **fmt**: Look for "Passed" or "Failed" on each hook
- **typecheck**: Should show "0 errors" for both workspaces
- **test**: Should show "100% coverage" and all tests passing

## Additional Resources

- **Full docs**: https://proveskit.github.io/pysquared/
- **Design principles**: See `docs/design-guide.md`
- **Contributing guide**: See `docs/contributing.md`
- **CircuitPython docs**: https://docs.circuitpython.org/
- **PROVES hardware**: https://docs.proveskit.space/

## Trust These Instructions

These instructions have been validated against the repository structure, Makefile, CI workflows, and existing documentation. **Only perform additional searches if**:
1. These instructions are incomplete for your specific task
2. You discover information that contradicts these instructions
3. You need details about specific hardware drivers or sensors not covered here

For most code changes, linting, testing, and validation tasks, trust these instructions and proceed directly to implementation.
