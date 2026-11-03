.DEFAULT_GOAL := help
.PHONY: help install test lint verify install-skills

help:
	@echo "Loop Maker development targets"
	@echo "  make install        Install editable package + dev dependencies"
	@echo "  make test           Run tests"
	@echo "  make lint           Run Ruff"
	@echo "  make verify         Run lint and tests"
	@echo "  make install-skills Install skills into the current project"

install:
	python -m pip install -e ".[dev,mcp]"

test:
	pytest -q

lint:
	ruff check src tests

verify: lint test

install-skills:
	bash scripts/install-skills.sh .
