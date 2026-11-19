# Terminal crossword

A small crossword you play in the browser. It is the practice repo for the workshop
**Terminal Tips and Tricks for Agentic Development**.

Follow the codelab: https://gerfalcon.github.io/portfolio/codelabs/terminal-crossword/
Workshop page and cheat sheet: https://gerfalcon.github.io/portfolio/workshops/terminal-tips/

Python 3.8 or newer and Git. Nothing else to install. It runs in Google Cloud Shell
or on your own computer.

```bash
python3 serve.py      # play: open port 8080 (Cloud Shell: Web Preview)
python3 check.py      # the project check: build, tests, puzzles, coverage
python3 doctor.py     # is this machine ready for the workshop?
```

On Windows, type `python` instead of `python3`.

| Path | What it is |
|---|---|
| `game/` | puzzles, rules, scoring and the HTML |
| `static/` | the browser code |
| `tests/` | one snapshot test to start with. You add the rest in the lab |
| `tasks/` | work for the agent: levels, leaderboard, more words |
| `tools/run_tests.py` | runs the tests with line coverage, standard library only |
| `tools/stop_hook.py`, `tools/hooks.json` | a Stop hook for Antigravity CLI: the agent may stop only when the check passes |
| `AGENTS.md` | rules for coding agents |
