.PHONY: install run debug clean lint lint-strict

install:
	@echo "Installing dependencies..."
	uv sync

run:
	@echo "Running function calling assistant..."
	uv run python -m src

debug:
	@echo "Running in debug mode..."
	uv run python -m pdb -m src

clean:
	rm -rf src/__pycache__ src/.mypy_cache

lint:
	@echo "Running flake8..."
	@flake8 src
	@echo "Running mypy..."
	@mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
