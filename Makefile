PYTHON		= uv run python3
UV			= uv
VENV		= .venv
PAC			= pac-man.py
TMP_DIRS	= __pycache__ .mypy_cache .ruff_cache

CONFIG ?= ""

install:
	@echo ">>> Installation de uv..."
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo ">>> Sync des dépendances (prod + dev)..."
	$(UV) sync
	@echo ">>> OK — projet prêt !"


run:
	@echo ">>> Lancement de la simulation..."
	$(PYTHON) $(PAC) $(CONFIG)

verbose:
	$(PYTHON) $(PAC) $(CONFIG) verbose
debug:
	@$(PYTHON) -m pdb -m $(PAC)

lint:
	@$(PYTHON) -m flake8 . --max-line-length=79 --exclude=.venv,llm_sdk
	@$(PYTHON) -m mypy src --explicit-package-bases --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@$(PYTHON) -m flake8 . --max-line-length=79 --exclude=.venv,llm_sdk
	@$(PYTHON) -m mypy src --explicit-package-bases --strict

clean:
	@echo ">>> Suppression des fichiers temporaires..."
	@rm -rf $(TMP_DIRS)
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -type d -name "__pycache__" -prune -exec rm -rf {}
	@echo ">>> Clean OK !"

fclean: clean
	@echo ">>> Suppression du venv..."
	@rm -rf $(VENV)
	@echo ">>> FClean OK !"

.PHONY: run install debug clean fclean lint lint-strict