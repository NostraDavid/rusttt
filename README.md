# rusttt

Python chess move generation using bitboards, with tests for checks, pins,
castling, promotions, en passant, and move undo.

## Start

Install Nix, devenv, and direnv, then run:

```bash
direnv allow
just setup
just run --help
```

`just run run` prints the starting board and performs a depth-six move count.
That command can take time. For a shorter check, run:

```bash
uv run --locked python -c 'from rusttt.logic import set_starting_position, run_perft_inline; set_starting_position(); run_perft_inline(2)'
```

The starting position produces 400 nodes at depth two.

## Develop

`just check` runs Ruff without edits, formatting verification, type checking,
pytest, and CLI help. `just update` refreshes the Nix and Python dependency locks.
