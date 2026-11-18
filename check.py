"""The project check. "Done" means this script passes.

    python3 check.py                      run every stage
    python3 check.py --min-coverage 90    also fail when coverage is below 90%
    python3 check.py --details            show the full test report
    python3 check.py --update-snapshots   accept the page as it looks now (a person decides)

Four stages:
  1. build      every Python file compiles
  2. tests      every test passes, and the tests this repo started with are still there, unchanged
  3. puzzles    every puzzle in game/puzzles.json fits together
  4. coverage   which lines of the game the tests ran

On Windows, type python instead of python3.
Python standard library only. Nothing to install.
"""
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The tests this repo started with, with their fingerprints (SHA-256).
# New tests may be added. These may not be removed, skipped or changed.
ORIGINAL_TESTS = {
    "test_first_puzzle_is_the_default": "378fed9e92e79d45990407cf5bda23ed4edbc0368c7546c6941e9b1c4b7a4fb3",
    "test_unknown_puzzle_is_an_error": "43ccbafbf30ea715b2a59d8daff8890fb209296f81a45b11b053b985f13e1c6f",
    "test_words_fit_together": "2ca26fab4b557d0512063907646f5c2010f5354ab0d6d65185db40e85a58db03",
    "test_clashing_words_are_reported": "d258b869e331cf885611ff4cc920d4edb0b14c4d9c11ca554051ebba550e7147",
    "test_word_off_the_board_is_reported": "4c9f4efc8708c5fbb4d8e31a3dce37622c020b65586b11c81bc218aae5df311d",
    "test_numbers_follow_reading_order": "c190ae8d890aa2054459e0b20eebe20253a0e1f88a68c03d65e6dffc6f6d0bc2",
    "test_empty_board_scores_nothing": "07f7e01c23202ae63a50ae4abfe9f9839ac7d237e16ddfd06ee36bbf839e7592",
    "test_one_right_word_scores_points": "9cf4c5f3cede4cc34db0725f4c903a83bb4e63553fe81744de74afb5ea6f8c70",
    "test_lowercase_and_spaces_are_fine": "66442ea241e69508d59a648d5326697f97944f4f9eff8c5e426993d8eea074bf",
    "test_full_solution_is_done": "3346608d4177a4a9ae1a8ce720b49b5c537745bf80c82522b3218c97af814b9c",
    "test_one_input_per_letter": "9c5f0b101c4a39792dd09e795269ed4badfc6ffa67a0930511e908e7f26d6672",
    "test_clues_show_number_and_length": "50230b4e9a68edab608206768f5cb35652828b14c557b5da3626dd52fe7f8843",
    "test_page_matches_snapshot": "3724c55eb89b7f16d1268ebdcbd01a00cfb6bec1ec1e4cd8697fb5bdc77e6d5a",
    "test_home_page_shows_the_board": "b4db7e519b6291b71ec920a62fe2a5a507635d9edd1a9da31cf57974b1b40f90",
    "test_static_files_are_served": "cd2350a8dbc05443551ebfd69345453b6482be87b35990f8bc5c793c65319aeb",
    "test_check_scores_answers": "e6ebe107b1354b2b463fb4c94bcd55073028ecd75e5a571ea974c97a943708f4",
    "test_bad_request_is_refused": "74aeb77a70b1807db7432f25a96dbac7c8c05cee410ce93194ce63ba807f110c",
    "test_unknown_pages_are_not_found": "9438ecc81fefdc3df4458e4741cf759e9627d7bb63c3a7107ebbb09a40101c91",
}


def relative(path):
    return path.relative_to(ROOT).as_posix()


def python_files():
    for path in sorted(ROOT.rglob("*.py")):
        if not any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            yield path


def source_text(path):
    # Files saved by some Windows tools start with a byte order mark. Accept them.
    return path.read_bytes().decode("utf-8-sig", errors="replace")


def stage_build(ctx):
    """Every Python file must compile."""
    problems = []
    for path in python_files():
        try:
            compile(path.read_bytes(), relative(path), "exec")
        except SyntaxError as err:
            problems.append(f"{relative(path)}:{err.lineno}: {err.msg}")
        except ValueError:
            problems.append(f"{relative(path)}: cannot read this file. Save it as UTF-8 text.")
    return problems, ""


def test_fingerprints():
    """Map each original test name to the fingerprints found for it in tests/."""
    found = {}
    for path in sorted((ROOT / "tests").rglob("*.py")):
        try:
            text = source_text(path)
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            continue  # already reported by the build stage
        lines = text.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ORIGINAL_TESTS:
                body = "\n".join(line.rstrip() for line in lines[node.lineno - 1:node.end_lineno])
                digest = hashlib.sha256(textwrap.dedent(body).encode("utf-8")).hexdigest()
                if node.decorator_list:
                    digest = "decorated"  # for example @unittest.skip
                found.setdefault(node.name, []).append(digest)
    return found


def run_tests(update_snapshots):
    """Run the tests once, in a fresh Python, with coverage switched on."""
    env = dict(os.environ)
    if update_snapshots:
        env["UPDATE_SNAPSHOTS"] = "1"
    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder) / "result.json"
        run = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "run_tests.py"), str(out)],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
        )
        if not out.exists():
            return None, (run.stderr or run.stdout).strip().splitlines()[-6:]
        return json.loads(out.read_text(encoding="utf-8")), []


def why(traceback):
    """The useful part of a failed test: the assertion message, or the last line."""
    marker = "\nAssertionError: "
    if marker in traceback:
        lines = traceback[traceback.rfind(marker) + len(marker):].strip().splitlines()
    else:
        lines = traceback.strip().splitlines()[-1:]
    return [line if len(line) <= 200 else line[:200] + " ..." for line in lines[:20]]


def stage_tests(ctx):
    """Every test must pass, and the original tests must stay as they were."""
    result, crash = run_tests(ctx["update_snapshots"])
    ctx["result"] = result
    if result is None:
        return ["The tests could not run:"] + crash, ""

    problems = []
    for item in result["broken"]:
        name = item["test"].split(".")[-1]
        reason = why(item["traceback"])
        problems.append(f"{name}: {reason[0]}")
        problems.extend("  " + line for line in reason[1:])
    if result["broken"]:
        if ctx["details"]:
            problems.extend(result["report"].strip().splitlines())
        else:
            problems.append("Full report: python3 check.py --details")

    found = test_fingerprints()
    changed = False
    for name, expected in ORIGINAL_TESTS.items():
        if name not in found:
            problems.append(f"{name} is missing. Tests may be added, never removed.")
            changed = True
        elif expected not in found[name]:
            problems.append(f"{name} was changed or skipped. Tests may be added. Existing tests may not change.")
            changed = True
    if changed:
        problems.append("See what changed with: git diff tests/")

    count, broken = result["run"], len(result["broken"])
    note = f"{broken} of {count} failed" if broken else f"{count} passed"
    if result["skipped"]:
        note += f", {len(result['skipped'])} skipped"
    return problems, note


def stage_puzzles(ctx):
    """Every puzzle fits together: words cross on the same letter, numbers match, clues exist."""
    try:
        from game.puzzle import PUZZLE_FILE, build_grid, numbers
        puzzles = json.loads(Path(PUZZLE_FILE).read_text(encoding="utf-8"))["puzzles"]
    except Exception as err:  # the agent may have changed anything; report, don't crash
        return [f"Cannot load the puzzles: {type(err).__name__}: {err}"], ""
    problems, ids = [], set()
    for puzzle in puzzles:
        name = puzzle.get("id", "?")
        if name in ids:
            problems.append(f"{name}: two puzzles have this id")
        ids.add(name)
        try:
            build_grid(puzzle)
            starts = numbers(puzzle)
        except Exception as err:
            problems.append(f"{name}: {err}")
            continue
        for word in puzzle["words"]:
            answer = word.get("answer", "")
            if not re.fullmatch(r"[A-Z]{2,}", answer):
                problems.append(f"{name} {word.get('id')}: answers are 2 or more capital letters A-Z, not {answer!r}")
            if not str(word.get("clue", "")).strip():
                problems.append(f"{name} {word.get('id')}: the clue is empty")
            expected = f"{starts[(word['row'], word['col'])]}{'A' if word['dir'] == 'across' else 'D'}"
            if word.get("id") != expected:
                problems.append(f"{name}: word {answer} should have the id {expected}, not {word.get('id')}")
    return problems, f"{len(puzzles)} puzzle{'s' if len(puzzles) != 1 else ''}"


def ranges(missing, lines):
    """Turn missing line numbers into short ranges, like 12-15, 20."""
    position = {line: i for i, line in enumerate(lines)}
    groups = []
    for line in missing:
        if groups and position[line] == position[groups[-1][-1]] + 1:
            groups[-1].append(line)
        else:
            groups.append([line])
    return ", ".join(f"{g[0]}-{g[-1]}" if len(g) > 1 else str(g[0]) for g in groups)


def stage_coverage(ctx):
    """How many code lines the tests ran. With --min-coverage N, below N% fails."""
    result = ctx.get("result")
    if result is None:
        return ["No coverage without a test run."], ""
    total = ran = 0
    table = []
    for name, info in sorted(result["files"].items()):
        lines, missing = info["lines"], info["missing"]
        if not lines or (len(lines) == 1 and not missing):
            continue  # nothing to show, for example an __init__.py with one docstring
        total += len(lines)
        ran += len(lines) - len(missing)
        percent = 100 * (len(lines) - len(missing)) // len(lines)
        row = f"{name:<20} {percent:>3}%"
        if missing:
            row += f"   not run: {ranges(missing, lines)}"
        table.append(row)
    percent = 100 * ran // total if total else 100
    ctx["table"] = table
    note = f"{percent}% of code lines ran in the tests"
    minimum = ctx["min_coverage"]
    if minimum is not None and percent < minimum:
        return [f"Coverage is {percent}%. The minimum is {minimum}%. Add tests for the lines marked 'not run'."], note
    return [], note


STAGES = [
    ("build", stage_build),
    ("tests", stage_tests),
    ("puzzles", stage_puzzles),
    ("coverage", stage_coverage),
]


def parse_args(argv):
    ctx = {"details": False, "update_snapshots": False, "min_coverage": None}
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--details":
            ctx["details"] = True
        elif arg == "--update-snapshots":
            ctx["update_snapshots"] = True
        elif arg.startswith("--min-coverage"):
            value = arg.split("=", 1)[1] if "=" in arg else (args.pop(0) if args else "")
            if not value.isdigit():
                raise SystemExit("--min-coverage needs a whole number, for example --min-coverage 90")
            ctx["min_coverage"] = int(value)
        else:
            raise SystemExit(f"Unknown option {arg}. See the top of check.py for the options.")
    return ctx


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")  # never crash on an unusual character
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    sys.dont_write_bytecode = True
    ctx = parse_args(argv)

    failed = []
    for number, (name, stage) in enumerate(STAGES, start=1):
        label = f"{number}/{len(STAGES)} {name}"
        if name != "build" and "build" in failed:
            print(f"[skip] {label} (fix the build first)")
            continue
        if name == "coverage" and ctx.get("result") is None:
            print(f"[skip] {label} (the tests did not run)")
            continue
        problems, note = stage(ctx)
        label += f" ({note})" if note else ""
        if problems:
            failed.append(name)
            print(f"[FAIL] {label}")
        else:
            print(f"[ok]   {label}")
        for line in problems + (ctx.get("table", []) if name == "coverage" else []):
            print(f"       {line}")

    print()
    if ctx["update_snapshots"]:
        print("Snapshots saved. Review them before you commit: git diff tests/snapshots")
    if failed:
        print("Check failed: " + ", ".join(failed) + ". Fix it and run the check again.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
