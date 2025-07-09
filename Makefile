.PHONY: black black-test check clean clean-build clean-pyc clean-test coverage install pylint pylint-quick pyre test publish poetry-check publish isort isort-check


VERSION := `cat VERSION`
package := "temporalloop"

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.mypy_cache' -exec rm -fr {} +
	find . -name '.pyre' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

test:
	uv run py.test --cov=$(package) --cov-report=html --cov-report=term-missing  --verbose tests


coverage:
	uv run coverage run --source $(package) setup.py test
	uv run coverage report -m
	uv run coverage html
	$(BROWSER) htmlcov/index.html

install: clean
	uv install

pylint-quick:
	uv run pylint --rcfile=.pylintrc $(package)  -E -r y

pylint:
	uv run pylint --rcfile=".pylintrc" $(package)

check: format-test uv-check ruff pylint pyre-check uv-check


pyre:
	uv run pyre

pyre-check:
	uv run pyre --noninteractive check 2>/dev/null

black:
	uv run black -t py310 tests $(package)

black-test:
	uv run black -t py310 tests $(package) --check

format:
	uv run ruff format $(package)

format-test:
	uv run ruff format $(package) --check

fix: format isort
	uv run ruff check --fix

ruff:
	uv run ruff check

publish: clean
	uv build
	uv publish

isort:
	uv run isort .

isort-check:
	uv run isort --diff --check .

.ONESHELL:
pyrightconfig:
	jq \
      --null-input \
      --arg venv "$$(basename $$(uv env info -p))" \
      --arg venvPath "$$(dirname $$(uv env info -p))" \
      '{ "venv": $$venv, "venvPath": $$venvPath }' \
      > pyrightconfig.json

rename:
	ack temporalloop -l | xargs -i{} sed -r -i "s/temporalloop/temporalloop/g" {}


upgrade-dep:
	uv lock -U --resolution=highest

uv-check:
	uv lock --locked --offline

BUMP ?= patch
bump:
	uv run bump-my-version bump $(BUMP)
