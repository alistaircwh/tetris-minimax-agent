"""Board renderer: produces SVG strings and PIL Images of a Tetress board.

Pure stdlib for SVG; Pillow only used for the raster path (used to build the
animated GIF for the README hero shot).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


BOARD_N = 11

# Layout (kept in sync with the SVG and PNG paths so they look identical).
CELL = 40
GAP = 2
GRID_PAD = 14
MARGIN_X = 24
HEADER_H = 88
FOOTER_H = 16

GRID_PX = BOARD_N * CELL + (BOARD_N - 1) * GAP
WIDTH = MARGIN_X * 2 + GRID_PAD * 2 + GRID_PX
HEIGHT = HEADER_H + GRID_PAD * 2 + GRID_PX + FOOTER_H

# Palette — picked to look good on both GitHub light and dark backgrounds.
BG = "#0F1419"
PANEL = "#161C26"
GRID_LINE = "#1F2733"
EMPTY_CELL = "#161C26"
RED = "#EF4444"
RED_GLOW = "#F87171"
BLUE = "#3B82F6"
BLUE_GLOW = "#60A5FA"
TEXT_MAIN = "#E5E7EB"
TEXT_DIM = "#9CA3AF"
ACCENT = "#FCD34D"


@dataclass(frozen=True)
class Frame:
    """One renderable snapshot of the game.

    `cleared` and `about_to_clear` are mutually exclusive:
      - `cleared` cells were wiped this turn (the frame shows the *after* state).
      - `about_to_clear` cells are still on the board but will be wiped on the
        next frame (the frame shows the *before* state, with the full row/col
        outlined so the rule is visually legible).
    """
    turn: int
    board: dict           # {(r, c): "R"|"B"}
    last_move: tuple      # ((r,c), ...) or None
    last_color: Optional[str]  # "R"|"B"|None
    cleared: tuple        # cells wiped this turn (post-clear frame)
    red_count: int
    blue_count: int
    about_to_clear: tuple = ()  # cells about to be wiped (pre-clear frame)


def cell_xy(r: int, c: int) -> tuple[int, int]:
    x = MARGIN_X + GRID_PAD + c * (CELL + GAP)
    y = HEADER_H + GRID_PAD + r * (CELL + GAP)
    return x, y


# ---------- SVG path ---------------------------------------------------------

def render_svg(frame: Frame, title: str = "TETRESS") -> str:
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif">'
    )

    # Drop-shadow filter for the most recently placed piece.
    parts.append(
        '<defs>'
        '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="3" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
        '<linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{RED_GLOW}"/><stop offset="100%" stop-color="{RED}"/>'
        '</linearGradient>'
        '<linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{BLUE_GLOW}"/><stop offset="100%" stop-color="{BLUE}"/>'
        '</linearGradient>'
        '</defs>'
    )

    # Background.
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>')

    # Header.
    parts.append(
        f'<text x="{MARGIN_X}" y="40" fill="{TEXT_MAIN}" font-size="22" font-weight="700" letter-spacing="3">{title}</text>'
    )
    parts.append(
        f'<text x="{MARGIN_X}" y="62" fill="{TEXT_DIM}" font-size="12" letter-spacing="1">'
        f'TURN {frame.turn:>3}</text>'
    )

    # Score badges on the right.
    badge_y = 30
    badge_h = 40
    badge_w = 70
    rx = WIDTH - MARGIN_X - badge_w
    bx = rx - badge_w - 8
    parts.append(
        f'<rect x="{bx}" y="{badge_y}" width="{badge_w}" height="{badge_h}" rx="8" fill="{PANEL}"/>'
        f'<circle cx="{bx + 14}" cy="{badge_y + badge_h // 2}" r="6" fill="url(#blueGrad)"/>'
        f'<text x="{bx + 28}" y="{badge_y + 26}" fill="{TEXT_MAIN}" font-size="16" font-weight="600">{frame.blue_count}</text>'
    )
    parts.append(
        f'<rect x="{rx}" y="{badge_y}" width="{badge_w}" height="{badge_h}" rx="8" fill="{PANEL}"/>'
        f'<circle cx="{rx + 14}" cy="{badge_y + badge_h // 2}" r="6" fill="url(#redGrad)"/>'
        f'<text x="{rx + 28}" y="{badge_y + 26}" fill="{TEXT_MAIN}" font-size="16" font-weight="600">{frame.red_count}</text>'
    )

    # Board panel (with subtle dashed border to hint at toroidal wrap).
    panel_x = MARGIN_X
    panel_y = HEADER_H
    panel_w = WIDTH - 2 * MARGIN_X
    panel_h = GRID_PAD * 2 + GRID_PX
    parts.append(
        f'<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" rx="12" fill="{PANEL}"/>'
    )
    parts.append(
        f'<rect x="{panel_x + 4}" y="{panel_y + 4}" width="{panel_w - 8}" height="{panel_h - 8}" rx="10" '
        f'fill="none" stroke="{GRID_LINE}" stroke-width="1" stroke-dasharray="4 4"/>'
    )

    last_cells = set(frame.last_move) if frame.last_move else set()
    doomed_cells = set(frame.about_to_clear)

    # All cells.
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            x, y = cell_xy(r, c)
            colour = frame.board.get((r, c))
            if colour is None:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="6" fill="{EMPTY_CELL}" stroke="{GRID_LINE}" stroke-width="1"/>'
                )
            else:
                grad = "url(#redGrad)" if colour == "R" else "url(#blueGrad)"
                is_new = (r, c) in last_cells
                is_doomed = (r, c) in doomed_cells
                if is_new or is_doomed:
                    parts.append(
                        f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="6" fill="{grad}" filter="url(#glow)"/>'
                    )
                    # New-placement gets an inner-yellow box; doomed gets a thicker outer ring.
                    if is_doomed:
                        parts.append(
                            f'<rect x="{x - 1}" y="{y - 1}" width="{CELL + 2}" height="{CELL + 2}" rx="7" '
                            f'fill="none" stroke="{ACCENT}" stroke-width="2.5" opacity="0.95"/>'
                        )
                    else:
                        parts.append(
                            f'<rect x="{x + 4}" y="{y + 4}" width="{CELL - 8}" height="{CELL - 8}" rx="4" '
                            f'fill="none" stroke="{ACCENT}" stroke-width="1.5" opacity="0.9"/>'
                        )
                else:
                    parts.append(
                        f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="6" fill="{grad}"/>'
                    )

    # Footer caption.
    caption = ""
    if frame.about_to_clear:
        lane = _describe_clear_lane(frame.about_to_clear)
        caption = f"{lane} fills up — clearing {len(frame.about_to_clear)} cells next"
    elif frame.last_color and frame.last_move:
        who = "RED" if frame.last_color == "R" else "BLUE"
        caption = f"{who} placed a tetromino"
        if frame.cleared:
            caption += f" · cleared {len(frame.cleared)} cells"
    parts.append(
        f'<text x="{MARGIN_X}" y="{HEIGHT - 4}" fill="{ACCENT if frame.about_to_clear else TEXT_DIM}" font-size="11" font-weight="{600 if frame.about_to_clear else 400}">{caption}</text>'
    )

    parts.append('</svg>')
    return "".join(parts)


# ---------- PNG path (for the GIF) -------------------------------------------

def render_png(frame: Frame, title: str = "TETRESS"):
    """Render a frame as a Pillow Image, sized identically to the SVG output."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img, "RGBA")

    title_font = _load_font(22, bold=True)
    small_font = _load_font(12, bold=True)
    score_font = _load_font(16, bold=True)
    caption_font = _load_font(11)

    # Header.
    draw.text((MARGIN_X, 18), title, fill=TEXT_MAIN, font=title_font)
    draw.text((MARGIN_X, 50), f"TURN {frame.turn:>3}", fill=TEXT_DIM, font=small_font)

    # Score badges.
    badge_y, badge_h, badge_w = 30, 40, 70
    rx = WIDTH - MARGIN_X - badge_w
    bx = rx - badge_w - 8
    _rounded_rect(draw, bx, badge_y, badge_w, badge_h, 8, PANEL)
    draw.ellipse((bx + 8, badge_y + badge_h // 2 - 6, bx + 20, badge_y + badge_h // 2 + 6), fill=BLUE)
    draw.text((bx + 28, badge_y + 11), str(frame.blue_count), fill=TEXT_MAIN, font=score_font)
    _rounded_rect(draw, rx, badge_y, badge_w, badge_h, 8, PANEL)
    draw.ellipse((rx + 8, badge_y + badge_h // 2 - 6, rx + 20, badge_y + badge_h // 2 + 6), fill=RED)
    draw.text((rx + 28, badge_y + 11), str(frame.red_count), fill=TEXT_MAIN, font=score_font)

    # Board panel.
    panel_x = MARGIN_X
    panel_y = HEADER_H
    panel_w = WIDTH - 2 * MARGIN_X
    panel_h = GRID_PAD * 2 + GRID_PX
    _rounded_rect(draw, panel_x, panel_y, panel_w, panel_h, 12, PANEL)
    _dashed_rounded_rect(draw, panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8, 10, GRID_LINE)

    last_cells = set(frame.last_move) if frame.last_move else set()
    doomed_cells = set(frame.about_to_clear)

    for r in range(BOARD_N):
        for c in range(BOARD_N):
            x, y = cell_xy(r, c)
            colour = frame.board.get((r, c))
            if colour is None:
                _rounded_rect(draw, x, y, CELL, CELL, 6, EMPTY_CELL, outline=GRID_LINE)
            else:
                fill = RED if colour == "R" else BLUE
                glow = RED_GLOW if colour == "R" else BLUE_GLOW
                is_new = (r, c) in last_cells
                is_doomed = (r, c) in doomed_cells
                _rounded_rect(draw, x, y, CELL, CELL, 6, fill)
                # Top highlight stripe to fake a gradient.
                draw.rectangle((x + 3, y + 3, x + CELL - 3, y + 7), fill=glow)
                if is_doomed:
                    _rounded_rect(draw, x - 1, y - 1, CELL + 2, CELL + 2, 7,
                                  None, outline=ACCENT, width=3)
                elif is_new:
                    _rounded_rect(draw, x + 4, y + 4, CELL - 8, CELL - 8, 4,
                                  None, outline=ACCENT, width=2)

    # Footer caption.
    caption = ""
    caption_colour = TEXT_DIM
    if frame.about_to_clear:
        lane = _describe_clear_lane(frame.about_to_clear)
        caption = f"{lane} fills up — clearing {len(frame.about_to_clear)} cells next"
        caption_colour = ACCENT
    elif frame.last_color and frame.last_move:
        who = "RED" if frame.last_color == "R" else "BLUE"
        caption = f"{who} placed a tetromino"
        if frame.cleared:
            caption += f"  ·  cleared {len(frame.cleared)} cells"
    draw.text((MARGIN_X, HEIGHT - 16), caption, fill=caption_colour, font=caption_font)

    return img


def _describe_clear_lane(cells: Iterable[tuple[int, int]]) -> str:
    """Return 'Row N', 'Column N', or 'Row N + Column M' for the caption."""
    cells = list(cells)
    if not cells:
        return ""
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    full_rows = sorted(r for r in rows if sum(1 for rr, _ in cells if rr == r) == BOARD_N)
    full_cols = sorted(c for c in cols if sum(1 for _, cc in cells if cc == c) == BOARD_N)
    bits = []
    if full_rows:
        bits.append("Row " + " + ".join(str(r) for r in full_rows))
    if full_cols:
        bits.append("Column " + " + ".join(str(c) for c in full_cols))
    return " + ".join(bits) if bits else "A line"


def _load_font(size: int, bold: bool = False):
    """Pick a reasonable system font, falling back to PIL's default bitmap."""
    from PIL import ImageFont

    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _rounded_rect(draw, x, y, w, h, r, fill, outline=None, width=1):
    if fill is not None:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=r, fill=fill)
    if outline is not None:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=r, outline=outline, width=width)


def _dashed_rounded_rect(draw, x, y, w, h, r, colour):
    """Approximate a dashed rounded border with short segments along each edge."""
    dash = 6
    gap = 4
    step = dash + gap
    # Top
    for sx in range(x + r, x + w - r, step):
        draw.line((sx, y, min(sx + dash, x + w - r), y), fill=colour)
    # Bottom
    for sx in range(x + r, x + w - r, step):
        draw.line((sx, y + h, min(sx + dash, x + w - r), y + h), fill=colour)
    # Left
    for sy in range(y + r, y + h - r, step):
        draw.line((x, sy, x, min(sy + dash, y + h - r)), fill=colour)
    # Right
    for sy in range(y + r, y + h - r, step):
        draw.line((x + w, sy, x + w, min(sy + dash, y + h - r)), fill=colour)
