# Crossword

A crossword you play in the browser. Python standard library only. Nothing to install.

## Commands
- Run the game: `python3 serve.py` (port 8080; `PORT=8081 python3 serve.py` for another port)
- Check everything: `python3 check.py`. Done means it passes.

## Where things are
- `game/puzzle.py` rules and scoring, `game/render.py` the HTML, `game/puzzles.json` the words
- `static/` the browser code, `tests/` the tests, `tasks/` the work to do

## Rules
- Never delete or change an existing test
- Ask before adding a dependency
- If you update a snapshot, say so, and show me `git diff tests/snapshots`
