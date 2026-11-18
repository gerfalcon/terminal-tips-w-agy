"""Turn a puzzle into HTML. The board is what the snapshot test checks."""
from html import escape

from .puzzle import build_grid, numbers


def render_board(puzzle):
    """The grid: one input per letter cell, dark cells everywhere else."""
    grid = build_grid(puzzle)
    nums = numbers(puzzle)
    rows = []
    for row in range(puzzle["rows"]):
        cells = []
        for col in range(puzzle["cols"]):
            if (row, col) not in grid:
                cells.append('<td class="block"></td>')
                continue
            num = nums.get((row, col))
            label = f'<span class="num">{num}</span>' if num else ""
            cells.append(
                f'<td>{label}<input data-cell="{row},{col}" maxlength="1" '
                f'aria-label="Row {row + 1}, column {col + 1}" autocomplete="off"></td>'
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<table class="board">\n' + "\n".join(rows) + "\n</table>\n"


def render_clues(puzzle):
    """Across and Down lists, with the word length after each clue."""
    sections = []
    for direction, heading in (("across", "Across"), ("down", "Down")):
        words = sorted((w for w in puzzle["words"] if w["dir"] == direction),
                       key=lambda w: int(w["id"][:-1]))
        items = "".join(
            f'<li data-word="{w["id"]}"><b>{w["id"][:-1]}</b> {escape(w["clue"])} ({len(w["answer"])})</li>'
            for w in words
        )
        sections.append(f"<section><h2>{heading}</h2><ol>{items}</ol></section>")
    return '<div class="clues">' + "".join(sections) + "</div>"


def render_page(puzzle):
    """The whole page the browser gets."""
    return PAGE.format(
        title=escape(puzzle["title"]),
        puzzle_id=escape(puzzle["id"]),
        board=render_board(puzzle),
        clues=render_clues(puzzle),
    )


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crossword: {title}</title>
<link rel="icon" href="data:,">
<link rel="stylesheet" href="static/style.css">
</head>
<body data-puzzle="{puzzle_id}">
<main>
<h1>{title}</h1>
<div class="game">
{board}
{clues}
</div>
<div class="actions">
<button id="check" type="button">Check</button>
<p id="score" role="status">Fill in the words, then press Check.</p>
</div>
</main>
<script src="static/app.js"></script>
</body>
</html>
"""
