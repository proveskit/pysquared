.PHONY: all
all: .venv circuitpython-workspaces/typeshed pre-commit-install

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

.venv: ## Create a virtual environment
	@echo "Creating virtual environment..."
	@$(MAKE) uv
	@$(UV) venv
	@$(UV) pip install --requirement pyproject.toml

circuitpython-workspaces/typeshed: ## Install CircuitPython typeshed stubs
	@echo "Installing CircuitPython typeshed stubs..."
	@$(MAKE) uv
	@$(UV) pip install circuitpython-typeshed==0.1.0 --target circuitpython-workspaces/typeshed

.PHONY: pre-commit-install
pre-commit-install: uv
	@echo "Installing pre-commit hooks..."
	@$(UVX) pre-commit install > /dev/null

.PHONY: fmt
fmt: pre-commit-install ## Lint and format files
	$(UVX) pre-commit run --all-files

.PHONY: typecheck
typecheck: .venv circuitpython-workspaces/typeshed ## Run type check
	@$(UV) run -m pyright --project=circuitpython-workspaces circuitpython-workspaces/
	@$(UV) run -m pyright --project=cpython-workspaces cpython-workspaces/

.PHONY: test
test: .venv ## Run tests
	$(UV) run coverage run --rcfile=pyproject.toml -m pytest cpython-workspaces/flight-software-unit-tests/src
	@$(UV) run coverage html --rcfile=pyproject.toml > /dev/null
	@$(UV) run coverage xml --rcfile=pyproject.toml > /dev/null

.PHONY: clean
clean: ## Remove all gitignored files
	git clean -dfX

##@ Build Tools
TOOLS_DIR ?= tools
$(TOOLS_DIR):
	mkdir -p $(TOOLS_DIR)

### Tool Versions
UV_VERSION ?= 0.8.14

UV_DIR ?= $(TOOLS_DIR)/uv-$(UV_VERSION)
UV ?= $(UV_DIR)/uv
UVX ?= $(UV_DIR)/uvx
.PHONY: uv
uv: $(UV) ## Download uv
$(UV): $(TOOLS_DIR)
	@test -s $(UV) || { mkdir -p $(UV_DIR); curl -LsSf https://astral.sh/uv/$(UV_VERSION)/install.sh | UV_INSTALL_DIR=$(UV_DIR) sh > /dev/null; }

.PHONY: docs
docs: uv
	@$(UV) run --group docs mkdocs serve

.PHONY: docs-deploy
docs-deploy: uv
	@$(UV) run --group docs mkdocs gh-deploy --config-file mkdocs.yaml --force
