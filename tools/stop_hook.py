"""Antigravity Stop hook: the agent may stop only when the project check passes.

.agents/hooks.json runs it like this:
    python3 tools/stop_hook.py --min-coverage 95

Antigravity sends a little JSON on stdin and reads JSON from stdout.
  {"decision": "continue", "reason": "..."}   the agent keeps working, and reads the reason
  {}                                           the agent may stop
After sending the agent back 3 times in a row, it lets the agent stop, so it cannot loop forever.
Then it is your turn: run the check yourself.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_TRIES = 4  # the 4th failed check in a row lets the agent stop


def main(argv):
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    if event.get("fullyIdle") is False:
        print("{}")  # background work is still running; nothing to judge yet
        return 0

    state = Path(tempfile.gettempdir()) / f"agy-stop-hook-{event.get('conversationId', 'none')}.txt"
    tries = int(state.read_text()) if state.exists() else 0

    run = subprocess.run([sys.executable, str(ROOT / "check.py"), *argv],
                         cwd=ROOT, capture_output=True, text=True, timeout=110)
    if run.returncode == 0 or tries + 1 >= MAX_TRIES:
        if state.exists():
            state.unlink()
        print("{}")
        return 0

    state.write_text(str(tries + 1))
    command = " ".join(["python3 check.py", *argv])
    output = "\n".join(run.stdout.strip().splitlines()[-25:])
    reason = (
        f"You are not done: `{command}` fails.\n{output}\n\n"
        "Keep going until it passes. Fix the code or add tests. "
        "Do not delete or change existing tests, and do not lower the coverage number. "
        "If the page changed on purpose, run `python3 check.py --update-snapshots` "
        "and tell the person to review `git diff tests/snapshots`."
    )
    print(json.dumps({"decision": "continue", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
