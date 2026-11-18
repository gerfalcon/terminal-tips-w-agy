"""Snapshot tests: compare HTML with a saved copy in tests/snapshots/.

To accept a new look on purpose, a person runs:  python3 check.py --update-snapshots
"""
import difflib
import os
from pathlib import Path

SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"


def assert_matches_snapshot(test, name, actual):
    path = SNAPSHOTS / name
    if os.environ.get("UPDATE_SNAPSHOTS") == "1":
        SNAPSHOTS.mkdir(exist_ok=True)
        path.write_text(actual, encoding="utf-8", newline="\n")
        return
    if not path.exists():
        test.fail(f"No snapshot yet for {name}. Look at the page, then run: python3 check.py --update-snapshots")
    expected = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if actual == expected:
        return
    diff = list(difflib.unified_diff(
        expected.splitlines(), actual.splitlines(),
        f"saved   tests/snapshots/{name}", "now", lineterm="", n=1,
    ))
    shown = diff[:16] + (["..."] if len(diff) > 16 else [])
    test.fail(
        "The page looks different from its snapshot.\n"
        + "\n".join(shown)
        + "\nChanged on purpose? A person checks the diff, then runs: python3 check.py --update-snapshots"
    )
