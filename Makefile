.PHONY: check dev format lint typecheck

VENV_DIR = .venv

check:
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory typecheck

dev:
	@set -x; python -m venv $(VENV_DIR)
	@. $(VENV_DIR)/bin/activate \
		&& PS4=$$PS1 && set -x \
		&& pip install -e ".[dev]"

format:
	@set -x; ruff format

lint:
	@set -x; ruff format --diff
	@set -x; ruff check

typecheck: 
	@set -x; ty check
