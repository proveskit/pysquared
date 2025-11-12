# PySquared Frozen Firmware Build System
# Builds custom CircuitPython firmware with PySquared libraries frozen

# Configuration
CIRCUITPYTHON_VERSION ?= 9.2.0
CIRCUITPYTHON_REPO ?= https://github.com/adafruit/circuitpython.git
BOARD ?= raspberry_pi_pico

# Directories
FIRMWARE_DIR := $(shell pwd)
CP_DIR := $(FIRMWARE_DIR)/circuitpython
FROZEN_DIR := $(CP_DIR)/frozen
BUILD_OUTPUT_DIR := $(FIRMWARE_DIR)/build
PYSQUARED_SRC := $(FIRMWARE_DIR)/../circuitpython-workspaces/flight-software/src/pysquared

# Board-specific settings
RASPBERRYPI_BOARDS := raspberry_pi_pico raspberry_pi_pico_w
PORT_DIR := $(CP_DIR)/ports/raspberrypi
FIRMWARE_FILE := $(PORT_DIR)/build-$(BOARD)/firmware.uf2

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: all
all: help

.PHONY: help
help: ## Display this help message
	@echo "PySquared Frozen Firmware Builder"
	@echo ""
	@echo "Usage: make <target> [BOARD=<board>] [CIRCUITPYTHON_VERSION=<version>]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2 } /^##@/ { printf "\n${YELLOW}%s${NC}\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make setup                              # Initial setup (clone CircuitPython, add dependencies)"
	@echo "  make firmware BOARD=raspberry_pi_pico   # Build firmware for Raspberry Pi Pico"
	@echo "  make all-boards                         # Build firmware for all supported boards"
	@echo "  make clean BOARD=raspberry_pi_pico      # Clean build artifacts"

##@ Setup

.PHONY: check-prereqs
check-prereqs: ## Check for required build tools
	@echo "${GREEN}Checking prerequisites...${NC}"
	@command -v git >/dev/null 2>&1 || { echo "${RED}git is required but not installed${NC}"; exit 1; }
	@command -v make >/dev/null 2>&1 || { echo "${RED}make is required but not installed${NC}"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "${RED}python3 is required but not installed${NC}"; exit 1; }
	@command -v arm-none-eabi-gcc >/dev/null 2>&1 || { echo "${RED}arm-none-eabi-gcc is required but not installed${NC}"; echo "Install with: sudo apt install gcc-arm-none-eabi"; exit 1; }
	@echo "${GREEN}All prerequisites satisfied${NC}"

.PHONY: setup
setup: check-prereqs clone-circuitpython setup-frozen-modules ## Complete first-time setup
	@echo "${GREEN}Setup complete!${NC}"
	@echo "Run 'make firmware BOARD=<board>' to build firmware"

.PHONY: clone-circuitpython
clone-circuitpython: ## Clone CircuitPython source
	@if [ -d "$(CP_DIR)" ]; then \
		echo "${YELLOW}CircuitPython already cloned, checking out version $(CIRCUITPYTHON_VERSION)${NC}"; \
		cd $(CP_DIR) && git fetch --tags && git checkout $(CIRCUITPYTHON_VERSION); \
	else \
		echo "${GREEN}Cloning CircuitPython $(CIRCUITPYTHON_VERSION)...${NC}"; \
		git clone --depth 1 --branch $(CIRCUITPYTHON_VERSION) $(CIRCUITPYTHON_REPO) $(CP_DIR); \
	fi
	@echo "${GREEN}Fetching CircuitPython submodules (raspberrypi port only)...${NC}"
	@cd $(CP_DIR) && python3 tools/ci_fetch_deps.py raspberrypi

.PHONY: setup-frozen-modules
setup-frozen-modules: ## Set up frozen module directory with PySquared and dependencies
	@echo "${GREEN}Setting up frozen modules...${NC}"
	@mkdir -p $(FROZEN_DIR)
	@$(MAKE) link-pysquared
	@$(MAKE) add-dependencies
	@echo "${GREEN}Frozen modules configured${NC}"

.PHONY: link-pysquared
link-pysquared: ## Create symlink to PySquared source in frozen directory
	@echo "Linking PySquared library to frozen directory..."
	@if [ -L "$(FROZEN_DIR)/pysquared" ] || [ -d "$(FROZEN_DIR)/pysquared" ]; then \
		rm -rf $(FROZEN_DIR)/pysquared; \
	fi
	@ln -s $(PYSQUARED_SRC) $(FROZEN_DIR)/pysquared
	@echo "${GREEN}PySquared linked${NC}"

.PHONY: add-dependencies
add-dependencies: ## Add PySquared dependencies as git submodules
	@echo "${YELLOW}Note: Dependencies must be added manually as git submodules${NC}"
	@echo "See docs/frozen-modules.md for instructions on adding each dependency"
	@echo ""
	@echo "Dependencies to add (from circuitpython-workspaces/flight-software/pyproject.toml):"
	@echo "  - adafruit-circuitpython-ina219"
	@echo "  - adafruit-circuitpython-asyncio"
	@echo "  - adafruit-circuitpython-drv2605"
	@echo "  - adafruit-circuitpython-lis2mdl"
	@echo "  - adafruit-circuitpython-lsm6ds"
	@echo "  - adafruit-circuitpython-mcp9808"
	@echo "  - adafruit-circuitpython-neopixel"
	@echo "  - adafruit-circuitpython-register"
	@echo "  - adafruit-circuitpython-rfm"
	@echo "  - adafruit-circuitpython-tca9548a"
	@echo "  - adafruit-circuitpython-ticks"
	@echo "  - adafruit-circuitpython-veml7700"
	@echo "  - adafruit-circuitpython-hashlib"
	@echo "  - proves-circuitpython-sx126"
	@echo "  - proves-circuitpython-sx1280"
	@echo ""
	@echo "Example command to add a dependency:"
	@echo "  cd $(FROZEN_DIR) && git submodule add https://github.com/adafruit/Adafruit_CircuitPython_INA219"

##@ Building

.PHONY: firmware
firmware: ## Build firmware for specified BOARD
	@if [ ! -d "$(CP_DIR)" ]; then \
		echo "${RED}CircuitPython not found. Run 'make setup' first.${NC}"; \
		exit 1; \
	fi
	@echo "${GREEN}Building firmware for $(BOARD)...${NC}"
	@echo "CircuitPython version: $(CIRCUITPYTHON_VERSION)"
	@echo "Board: $(BOARD)"
	@mkdir -p $(BUILD_OUTPUT_DIR)
	@cd $(PORT_DIR) && make BOARD=$(BOARD)
	@if [ -f "$(FIRMWARE_FILE)" ]; then \
		cp $(FIRMWARE_FILE) $(BUILD_OUTPUT_DIR)/$(BOARD)-frozen-$(CIRCUITPYTHON_VERSION).uf2; \
		echo "${GREEN}Firmware built successfully!${NC}"; \
		echo "Output: $(BUILD_OUTPUT_DIR)/$(BOARD)-frozen-$(CIRCUITPYTHON_VERSION).uf2"; \
	else \
		echo "${RED}Build failed - firmware file not found${NC}"; \
		exit 1; \
	fi

.PHONY: all-boards
all-boards: ## Build firmware for all supported boards
	@for board in $(RASPBERRYPI_BOARDS); do \
		$(MAKE) firmware BOARD=$$board || exit 1; \
	done
	@echo "${GREEN}All boards built successfully!${NC}"

##@ Maintenance

.PHONY: clean
clean: ## Clean build artifacts for specified BOARD
	@if [ -d "$(PORT_DIR)" ]; then \
		echo "${YELLOW}Cleaning build for $(BOARD)...${NC}"; \
		cd $(PORT_DIR) && make BOARD=$(BOARD) clean; \
		rm -f $(BUILD_OUTPUT_DIR)/$(BOARD)-frozen-*.uf2; \
	fi

.PHONY: clean-all
clean-all: ## Remove all build artifacts and CircuitPython source
	@echo "${RED}Removing all build artifacts and CircuitPython source...${NC}"
	@rm -rf $(CP_DIR)
	@rm -rf $(BUILD_OUTPUT_DIR)
	@echo "${GREEN}Clean complete${NC}"

.PHONY: list-boards
list-boards: ## List available board configurations
	@if [ -d "$(PORT_DIR)/boards" ]; then \
		echo "${GREEN}Available RP2040/RP2350 boards:${NC}"; \
		ls -1 $(PORT_DIR)/boards | grep -E "(pico|proves)" || echo "No boards found"; \
	else \
		echo "${RED}CircuitPython not set up. Run 'make setup' first.${NC}"; \
	fi

.PHONY: update-circuitpython
update-circuitpython: ## Update CircuitPython to a different version
	@if [ -d "$(CP_DIR)" ]; then \
		echo "${YELLOW}Updating CircuitPython to $(CIRCUITPYTHON_VERSION)...${NC}"; \
		cd $(CP_DIR) && git fetch --tags && git checkout $(CIRCUITPYTHON_VERSION); \
		cd $(CP_DIR) && python3 tools/ci_fetch_deps.py raspberrypi; \
		echo "${GREEN}CircuitPython updated${NC}"; \
	else \
		echo "${RED}CircuitPython not cloned. Run 'make setup' first.${NC}"; \
		exit 1; \
	fi

##@ Information

.PHONY: info
info: ## Show build configuration
	@echo "${GREEN}PySquared Frozen Firmware Build Configuration${NC}"
	@echo ""
	@echo "CircuitPython Version: $(CIRCUITPYTHON_VERSION)"
	@echo "CircuitPython Directory: $(CP_DIR)"
	@echo "Frozen Modules Directory: $(FROZEN_DIR)"
	@echo "Build Output Directory: $(BUILD_OUTPUT_DIR)"
	@echo "PySquared Source: $(PYSQUARED_SRC)"
	@echo ""
	@echo "Current Board: $(BOARD)"
	@echo "Port Directory: $(PORT_DIR)"
	@echo ""
	@if [ -d "$(FROZEN_DIR)" ]; then \
		echo "Frozen Modules:"; \
		ls -1 $(FROZEN_DIR) 2>/dev/null | sed 's/^/  - /' || echo "  (none)"; \
	else \
		echo "Frozen Modules: (not set up)"; \
	fi
