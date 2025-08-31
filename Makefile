.PHONY: all
all: .venv pre-commit-install

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

.venv: ## Create a virtual environment
	@echo "Creating virtual environment..."
	@$(MAKE) uv
	@$(UV) venv
	@$(UV) pip install --requirement pyproject.toml
	@$(UV) pip install circuitpython-typeshed --target typeshed

.PHONY: pre-commit-install
pre-commit-install: uv
	@echo "Installing pre-commit hooks..."
	@$(UVX) pre-commit install > /dev/null

.PHONY: fmt
fmt: pre-commit-install ## Lint and format files
	$(UVX) pre-commit run --all-files

typecheck: .venv ## Run type check
	@$(UV) run -m pyright .

.PHONY: test
test: .venv ## Run tests
	$(UV) run coverage run --rcfile=pyproject.toml -m pytest tests/unit
	@$(UV) run coverage html --rcfile=pyproject.toml > /dev/null
	@$(UV) run coverage xml --rcfile=pyproject.toml > /dev/null

.PHONY: clean
clean: ## Remove all gitignored files
	git clean -dfX

##@ Build

.PHONY: build
build: uv mpy-cross ## Build the project, store the result in the artifacts directory
	@echo "Creating artifacts/pysquared"
	@mkdir -p artifacts/pysquared
	$(call compile_mpy)
	$(call rsync_to_dest,.,artifacts/pysquared/)
	@$(UV) run python -c "import os; [os.remove(os.path.join(root, file)) for root, _, files in os.walk('artifacts/pysquared') for file in files if file.endswith('.py')]"
	@$(UV) run python -c "import os; [os.remove(os.path.join(root, file)) for root, _, files in os.walk('pysquared') for file in files if file.endswith('.mpy')]"
	@echo "Creating artifacts/pysquared.zip"
	@zip -r artifacts/pysquared.zip artifacts/pysquared > /dev/null

define rsync_to_dest
	@if [ -z "$(1)" ]; then \
		echo "Issue with Make target, rsync source is not specified. Stopping."; \
		exit 1; \
	fi

	@if [ -z "$(2)" ]; then \
		echo "Issue with Make target, rsync destination is not specified. Stopping."; \
		exit 1; \
	fi

	@rsync -avh $(1)/pysquared/* --exclude='requirements.txt' --exclude='__pycache__' $(2) --delete --times --checksum
endef

##@ Build Tools
TOOLS_DIR ?= tools
$(TOOLS_DIR):
	mkdir -p $(TOOLS_DIR)

### Tool Versions
UV_VERSION ?= 0.8.14
MPY_CROSS_VERSION ?= 9.0.5

UV_DIR ?= $(TOOLS_DIR)/uv-$(UV_VERSION)
UV ?= $(UV_DIR)/uv
UVX ?= $(UV_DIR)/uvx
.PHONY: uv
uv: $(UV) ## Download uv
$(UV): $(TOOLS_DIR)
	@test -s $(UV) || { mkdir -p $(UV_DIR); curl -LsSf https://astral.sh/uv/$(UV_VERSION)/install.sh | UV_INSTALL_DIR=$(UV_DIR) sh > /dev/null; }

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

MPY_S3_PREFIX ?= https://adafruit-circuit-python.s3.amazonaws.com/bin/mpy-cross
MPY_CROSS ?= $(TOOLS_DIR)/mpy-cross-$(MPY_CROSS_VERSION)
.PHONY: mpy-cross
mpy-cross: $(MPY_CROSS) ## Download mpy-cross
$(MPY_CROSS): $(TOOLS_DIR)
	@echo "Downloading mpy-cross $(MPY_CROSS_VERSION)..."
	@mkdir -p $(dir $@)
ifeq ($(OS),Windows_NT)
	@curl -LsSf $(MPY_S3_PREFIX)/windows/mpy-cross-windows-$(MPY_CROSS_VERSION).static.exe -o $@
else
ifeq ($(UNAME_S),Linux)
ifeq ($(or $(filter x86_64,$(UNAME_M)),$(filter amd64,$(UNAME_M))),$(UNAME_M))
	@curl -LsSf $(MPY_S3_PREFIX)/linux-amd64/mpy-cross-linux-amd64-$(MPY_CROSS_VERSION).static -o $@
	@chmod +x $@
endif
else ifeq ($(UNAME_S),Darwin)
	@curl -LsSf $(MPY_S3_PREFIX)/macos-11/mpy-cross-macos-11-$(MPY_CROSS_VERSION)-universal -o $@
	@chmod +x $@
else
	@echo "Pre-built mpy-cross not available for system: $(UNAME_S)"
endif
endif

define compile_mpy
	@$(UV) run python -c "import os, subprocess; [subprocess.run(['$(MPY_CROSS)', os.path.join(root, file)]) for root, _, files in os.walk('pysquared') for file in files if file.endswith('.py')]" || exit 1
endef

.PHONY: docs
docs: uv
	@$(UV) run --group docs mkdocs serve

.PHONY: docs-deploy
docs-deploy: uv
	@$(UV) run --group docs mkdocs gh-deploy --config-file mkdocs.yaml --force
