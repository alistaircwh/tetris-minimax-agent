# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

COMP30024 Artificial Intelligence, Semester 1 2024 (University of Melbourne). The game is **Tetress**: players alternate placing tetromino pieces on an 11×11 wrapping board; full rows/columns are cleared after each placement; a player loses when they have no legal moves.

- **Part A** (`part_a/search/`): Single-player A* search to find a sequence of placements that fills the row or column containing a target coordinate.
- **Part B** (`part_b/`): Two-player game-playing agent with multiple agent implementations.

## Running

### Part A

From `part_a/`:
```bash
python -m search < test-vis1.csv
```
Input is a CSV with `r`/`R` for red cells, `b`/`B` for blue (uppercase `B` marks the target coordinate).

### Part B — Run a game

From `part_b/`:
```bash
python -m referee agent agent_random          # agent (RED) vs random (BLUE)
python -m referee agent_random agent          # random (RED) vs agent (BLUE)
python -m referee agent agent_minimax         # agent vs minimax variant
python -m referee agent agent -v 0            # silent (result only)
python -m referee agent agent_random -t 180   # with 180 s time limit per player
python -m referee agent agent_random -l game.log  # log to file
```

Verbosity: `-v 0` result only, `-v 1` commentary, `-v 2` (default) commentary + board, `-v 3` debug.

### Part B — Batch testing

From `part_b/`:
```bash
bash test.sh   # runs 100 games, appends results to testing/agent_test.txt
```

## Architecture

### Part A — A* Search

| File | Role |
|------|------|
| `search/program.py` | A* implementation; `search(board, target)` is the entry point |
| `search/core.py` | Core types: `Coord`, `PlayerColor`, `PlaceAction`, `PriorityQueue` |
| `search/templates.py` | All tetromino shapes as `PlaceTemplate` offset vectors |
| `search/utils.py` | `render_board()` for debugging |
| `search/__main__.py` | Parses stdin CSV → calls `search()` → prints `$SOLUTION` lines |

The heuristic is admissible: `min(ceil(row_distance/4) + ceil(empty_in_row/4), ceil(col_distance/4) + ceil(empty_in_col/4))`. The board wraps, so distances use modular arithmetic.

### Part B — Agent and Referee

**Board representation**: `dict[Coord, PlayerColor]` — only occupied cells appear as keys; `board.get(coord)` returns `None` for empty cells.

**Move generation** (`generate_legal_moves`): For each friendly piece, consult `precomputed_moves[coord][direction]` (precomputed at startup in `templates.py`), then prune directions where the adjacent cell is occupied before checking full legality.

**Apply/undo pattern**: Moves are applied in-place and undone after evaluation — no board copying. `clear_full_rows_and_columns` returns a `cleared_info` dict so it can be reversed with `undo_clear_full_rows_and_columns`.

**Agent variants** (all in `part_b/`):

| Package | Strategy |
|---------|----------|
| `agent/` | Final submission: greedy 1-ply with opening book; separate early-game (turns < 45) and late-game heuristics |
| `agent_minimax/` | Minimax with alpha-beta pruning (depth 1) |
| `agent_greedy/` | Greedy 1-ply, earlier iteration |
| `agent_random/` | Uniformly random legal move; used as baseline |

**Heuristic design** (final agent): Scores are `Σ min(6, pieces_in_row) + Σ min(6, pieces_in_col)` plus a spread bonus for unique rows/columns occupied. Late game also rewards mobility > 25. The opponent's score is weighted 1.25× (early) or 1.5× (late) to encourage aggression.

**Referee** (`referee/`): Wraps each agent in `AgentProxyPlayer`, enforces time/space limits, runs the async game loop, and prints the result. Agents must implement `__init__(color, **referee)`, `action(**referee) -> Action`, and `update(color, action, **referee)`.
