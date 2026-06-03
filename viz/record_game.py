"""Run a Tetress game between two agents, record every frame, then emit:

  * an animated GIF of the full playthrough               -> assets/playthrough.gif
  * three static SVG snapshots at key moments             -> assets/snapshot_*.svg
  * a JSON dump of the move list for the interactive viewer -> viz/game.json

Usage (from repo root):

    python3 viz/record_game.py

The game is deterministic: a fixed seed is used so the GIF/snapshots reproduce.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "part_b"))

from referee.game import PlayerColor, Coord, PlaceAction, BOARD_N  # noqa: E402
from agent.program import Agent as FinalAgent  # noqa: E402
from agent_random.program import Agent as RandomAgent  # noqa: E402

from render import Frame, render_svg, render_png  # noqa: E402


def board_dict_to_simple(board: dict[Coord, PlayerColor]) -> dict[tuple[int, int], str]:
    """Convert {Coord: PlayerColor} -> {(r, c): 'R'|'B'}, dropping cleared cells."""
    out = {}
    for coord, colour in board.items():
        if colour is None:
            continue
        key = (coord.r, coord.c)
        out[key] = "R" if colour == PlayerColor.RED else "B"
    return out


def play_game(seed: int = 7) -> list[Frame]:
    """Play final agent (RED) vs random (BLUE), record one frame per ply."""
    random.seed(seed)

    red = FinalAgent(PlayerColor.RED)
    blue = RandomAgent(PlayerColor.BLUE)
    referee_board: dict[Coord, PlayerColor] = {}
    frames: list[Frame] = []

    # Frame 0: empty board.
    frames.append(Frame(turn=0, board={}, last_move=None, last_color=None,
                        cleared=(), red_count=0, blue_count=0))

    turn = 0
    current = red
    current_color = PlayerColor.RED
    other = blue

    while turn < 80:  # safety cap; games usually end well before this
        turn += 1
        move = current.action()
        if move is None:
            break

        # Apply to referee board.
        for coord in move.coords:
            referee_board[coord] = current_color

        placed_cells = tuple((c.r, c.c) for c in move.coords)
        last_colour_letter = "R" if current_color == PlayerColor.RED else "B"

        # Before clearing, check which lines (if any) are now full. If something
        # is about to clear, emit a "pre-clear" frame so the line-clear rule is
        # visually legible: full row/col stays on the board, outlined in accent.
        pending = _full_lines(referee_board)
        if pending:
            board_with_placement = board_dict_to_simple(referee_board)
            frames.append(Frame(
                turn=turn,
                board=board_with_placement,
                last_move=placed_cells,
                last_color=last_colour_letter,
                cleared=(),
                red_count=sum(1 for v in board_with_placement.values() if v == "R"),
                blue_count=sum(1 for v in board_with_placement.values() if v == "B"),
                about_to_clear=tuple(pending),
            ))

        cleared = _clear_lines(referee_board)

        # Tell both agents about the move.
        red.update(current_color, move)
        blue.update(current_color, move)

        simple_board = board_dict_to_simple(referee_board)
        last_cells = tuple((c.r, c.c) for c in move.coords if (c.r, c.c) in simple_board)
        # If the move was placed and then immediately cleared, last_cells will be empty;
        # fall back to the original placement so the highlight still shows briefly.
        if not last_cells:
            last_cells = placed_cells

        red_count = sum(1 for v in simple_board.values() if v == "R")
        blue_count = sum(1 for v in simple_board.values() if v == "B")

        frames.append(Frame(
            turn=turn,
            board=simple_board,
            last_move=last_cells,
            last_color=last_colour_letter,
            cleared=tuple(cleared),
            red_count=red_count,
            blue_count=blue_count,
        ))

        # Swap players.
        current, other = other, current
        current_color = PlayerColor.BLUE if current_color == PlayerColor.RED else PlayerColor.RED

        # Check if next player has any moves; if not, game ends.
        if not _has_legal_moves(referee_board, current_color):
            break

    return frames


def _full_lines(board: dict[Coord, PlayerColor]) -> list[tuple[int, int]]:
    """Return the cells in every fully-filled row/column. Non-destructive."""
    full_rows, full_cols = [], []
    for r in range(BOARD_N):
        if all(board.get(Coord(r, c)) is not None for c in range(BOARD_N)):
            full_rows.append(r)
    for c in range(BOARD_N):
        if all(board.get(Coord(r, c)) is not None for r in range(BOARD_N)):
            full_cols.append(c)
    cells: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for r in full_rows:
        for c in range(BOARD_N):
            if (r, c) not in seen:
                cells.append((r, c))
                seen.add((r, c))
    for c in full_cols:
        for r in range(BOARD_N):
            if (r, c) not in seen:
                cells.append((r, c))
                seen.add((r, c))
    return cells


def _clear_lines(board: dict[Coord, PlayerColor]) -> list[tuple[int, int]]:
    """Clear any fully occupied rows/columns. Return the cleared cell coordinates."""
    full_rows = []
    full_cols = []
    for r in range(BOARD_N):
        if all(board.get(Coord(r, c)) is not None for c in range(BOARD_N)):
            full_rows.append(r)
    for c in range(BOARD_N):
        if all(board.get(Coord(r, c)) is not None for r in range(BOARD_N)):
            full_cols.append(c)
    cleared = []
    for r in full_rows:
        for c in range(BOARD_N):
            if Coord(r, c) in board:
                cleared.append((r, c))
                del board[Coord(r, c)]
    for c in full_cols:
        for r in range(BOARD_N):
            if Coord(r, c) in board:
                cleared.append((r, c))
                del board[Coord(r, c)]
    return cleared


def _has_legal_moves(board: dict[Coord, PlayerColor], colour: PlayerColor) -> bool:
    """Cheap check: does `colour` have any pieces left that can plausibly expand?"""
    # If the colour has no pieces at all, they still get to make the opening move.
    if not any(v == colour for v in board.values()):
        return True
    # Otherwise use the agent's own generator via a one-shot dummy.
    dummy = FinalAgent(colour)
    dummy.board = dict(board)
    return bool(dummy.generate_legal_moves(dummy.board, colour))


# ---------- Output -----------------------------------------------------------

def write_gif(
    frames: list[Frame],
    path: Path,
    frame_ms: int = 280,
    hold_ms: int = 1800,
    max_frames: int = 55,
) -> None:
    """Build an animated GIF that loops forever.

    Caps at `max_frames` so the hero GIF stays under ~15s of playback.
    """
    from PIL import Image

    if len(frames) > max_frames:
        frames = frames[:max_frames]
    images = [render_png(f) for f in frames]
    durations = [frame_ms] * len(images)
    # Pre-clear frames get a longer hold so the about-to-clear ring is readable.
    for i, f in enumerate(frames):
        if f.about_to_clear:
            durations[i] = 900
    durations[0] = 600        # linger on the empty board briefly
    durations[-1] = hold_ms   # hold the final position before looping
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )


def write_svg(frame: Frame, path: Path) -> None:
    path.write_text(render_svg(frame), encoding="utf-8")


def write_game_json(frames: list[Frame], path: Path) -> None:
    """Dump frames in a viewer-friendly shape."""
    data = {
        "board_n": BOARD_N,
        "frames": [
            {
                "turn": f.turn,
                "board": [{"r": r, "c": c, "color": col} for (r, c), col in f.board.items()],
                "last_move": list(f.last_move) if f.last_move else None,
                "last_color": f.last_color,
                "cleared": list(f.cleared),
                "about_to_clear": list(f.about_to_clear),
                "red_count": f.red_count,
                "blue_count": f.blue_count,
            }
            for f in frames
        ],
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def pick_snapshot_frames(frames: list[Frame]) -> dict[str, Frame]:
    """Pick three frames that show off distinct moments of the game.

    We want visual variety: an early-game shot with just a few pieces, a
    line-clear moment that makes the row/column rule legible, and a packed
    late-game position.
    """
    n = len(frames)
    chosen: dict[str, Frame] = {}

    # Opening: first frame with the opening books played out.
    for f in frames:
        if f.red_count + f.blue_count >= 8:
            chosen["opening"] = f
            break
    chosen.setdefault("opening", frames[min(4, n - 1)])

    # Line clear: prefer a *pre-clear* frame so the about-to-clear row/column is
    # still on the board with an accent ring around it — makes the rule legible.
    pre_clears = [f for f in frames if f.about_to_clear]
    if pre_clears:
        chosen["lineclear"] = max(
            pre_clears[: max(1, len(pre_clears) // 2)],
            key=lambda f: len(f.about_to_clear),
        )
    else:
        post_clears = [f for f in frames if f.cleared]
        chosen["lineclear"] = (
            max(post_clears, key=lambda f: len(f.cleared)) if post_clears else frames[n // 2]
        )

    # Late game: heaviest board (most occupied cells overall).
    busy = max(frames, key=lambda f: f.red_count + f.blue_count)
    chosen["midgame"] = busy

    return chosen


def main() -> None:
    out_assets = ROOT / "assets"
    out_assets.mkdir(exist_ok=True)
    out_viz = ROOT / "viz"

    print("Playing game ...")
    frames = play_game(seed=7)
    print(f"Recorded {len(frames)} frames ({frames[-1].turn} turns).")

    print("Writing animated GIF ...")
    write_gif(frames, out_assets / "playthrough.gif")

    print("Writing static SVG snapshots ...")
    snapshots = pick_snapshot_frames(frames)
    for label, frame in snapshots.items():
        write_svg(frame, out_assets / f"snapshot_{label}.svg")
        print(f"  {label}: turn {frame.turn} -> snapshot_{label}.svg")

    print("Writing game.json for the interactive viewer ...")
    write_game_json(frames, out_viz / "game.json")

    print("Done.")


if __name__ == "__main__":
    main()
