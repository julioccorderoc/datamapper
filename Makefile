.PHONY: setup lint test precommit clean check deps

setup: 
	@echo "🚀 Setting up development environment"
	@uv sync

test: # tests and coverage
	@echo "🚀 Running tests"
	@uv run pytest --cov --cov-config=pyproject.toml --cov-report=html tests

precommit: # run pre-commit hooks
	@echo "🚀 Running pre-commit hooks"
	@uv run pre-commit run -a

check: # run code quality tools
	@echo "🚀 Checking code quality"
	@uv lock --locked
	@uv run mypy .
	@uv run ruff check .
	@uv run deptry .
	@uv run isort .

clean: # clean up
	@echo "🚀 Cleaning up"
	rm -rf .pytest_cache .mypy_cache
	rm -rf .ruff_cache .ruff-cache .ruff-history .ruff-temp
	rm -rf .coverage .coverage.*
	rm -rf htmlcov
	@uv clean

build: # build package
	@echo "🚀 Building package"
	@uv build
	@uvx twine check dist/*

publish: # publish package
	@echo "🚀 Publishing package"
	@uv publish