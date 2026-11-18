"""Crossword puzzles: load them, lay out the grid, check answers."""
import json
from pathlib import Path

PUZZLE_FILE = Path(__file__).resolve().parent / "puzzles.json"
POINTS_PER_WORD = 10


def load_puzzle(puzzle_id=None):
    """Return one puzzle as a dict. Without an id, the first puzzle in the file."""
    puzzles = json.loads(PUZZLE_FILE.read_text(encoding="utf-8"))["puzzles"]
    if puzzle_id is None:
        return puzzles[0]
    for puzzle in puzzles:
        if puzzle["id"] == puzzle_id:
            return puzzle
    raise KeyError(f"no puzzle called {puzzle_id!r}")


def cells_of(word):
    """The (row, col) cells a word covers, in reading order."""
    dr, dc = (0, 1) if word["dir"] == "across" else (1, 0)
    return [(word["row"] + i * dr, word["col"] + i * dc) for i in range(len(word["answer"]))]


def build_grid(puzzle):
    """Map each letter cell to its letter. Raise ValueError if two words disagree."""
    grid = {}
    for word in puzzle["words"]:
        for cell, letter in zip(cells_of(word), word["answer"].upper()):
            row, col = cell
            if not (0 <= row < puzzle["rows"] and 0 <= col < puzzle["cols"]):
                raise ValueError(f"{word['id']} runs off the board at {cell}")
            if grid.get(cell, letter) != letter:
                raise ValueError(f"{word['id']} puts {letter} where {grid[cell]} already is, at {cell}")
            grid[cell] = letter
    return grid


def numbers(puzzle):
    """The clue number shown in the first cell of each word, in reading order."""
    starts = sorted({(word["row"], word["col"]) for word in puzzle["words"]})
    return {cell: n for n, cell in enumerate(starts, start=1)}


def check_answers(puzzle, entries):
    """Score the player's letters.

    entries maps "row,col" to a letter, for example {"0,0": "p"}.
    """
    typed = {}
    for key, value in entries.items():
        row, col = (int(part) for part in key.split(","))
        typed[(row, col)] = str(value).strip().upper()[:1]

    correct, cells = [], set()
    for word in puzzle["words"]:
        word_cells = cells_of(word)
        guess = "".join(typed.get(cell, "") for cell in word_cells)
        if guess == word["answer"].upper():
            correct.append(word["id"])
            cells.update(f"{row},{col}" for row, col in word_cells)

    return {
        "correct": correct,
        "cells": sorted(cells),
        "score": POINTS_PER_WORD * len(correct),
        "total": len(puzzle["words"]),
        "done": len(correct) == len(puzzle["words"]),
    }
