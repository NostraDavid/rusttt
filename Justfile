set shell := ["bash", "-euc"]
set positional-arguments

default:
    @just --list

setup:
    uv sync --locked

run *args:
    uv run --locked rusttt "$@"

lint:
    uv run --locked ruff check --no-fix src tests

format-check:
    uv run --locked ruff format --check src tests

typecheck:
    uv run --locked ty check

test:
    uv run --locked pytest

check: lint format-check typecheck test
    uv run --locked rusttt --help

update:
    devenv update
    uv lock --upgrade
    uv sync --locked
