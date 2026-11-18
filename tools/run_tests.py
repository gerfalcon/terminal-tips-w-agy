"""Run the tests and record which lines of the game they ran. check.py calls this.

    python3 tools/run_tests.py RESULT.json

Coverage is measured with the standard library only (sys.settrace), so there is
nothing to install. Every .py file in the repo counts, except tests/, tools/,
check.py and doctor.py.
"""
import dis
import io
import json
import os
import sys
import threading
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOT_COUNTED = {"tests", "tools", "check.py", "doctor.py"}


def counted_files():
    files = []
    for path in sorted(ROOT.rglob("*.py")):
        parts = path.relative_to(ROOT).parts
        if parts[0] in NOT_COUNTED or any(p.startswith(".") for p in parts):
            continue
        files.append(path)
    return files


def executable_lines(path):
    """Line numbers that hold code, found from the compiled file."""
    try:
        code = compile(path.read_bytes(), str(path), "exec")
    except (SyntaxError, ValueError):
        return set()
    lines, todo = set(), [code]
    while todo:
        current = todo.pop()
        lines.update(line for _, line in dis.findlinestarts(current) if line)
        todo.extend(c for c in current.co_consts if isinstance(c, types.CodeType))
    return lines


def main():
    out = Path(sys.argv[1])
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    sys.dont_write_bytecode = True

    wanted = {os.path.realpath(p): p.relative_to(ROOT).as_posix() for p in counted_files()}
    seen = {name: set() for name in wanted.values()}
    names = {}

    def name_of(filename):
        if filename not in names:
            names[filename] = wanted.get(os.path.realpath(filename))
        return names[filename]

    def local(frame, event, arg):
        if event == "line":
            seen[name_of(frame.f_code.co_filename)].add(frame.f_lineno)
        return local

    def tracer(frame, event, arg):
        name = name_of(frame.f_code.co_filename)
        if name is None:
            return None
        seen[name].add(frame.f_lineno)
        return local

    threading.settrace(tracer)
    sys.settrace(tracer)
    report = io.StringIO()
    try:
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
        result = unittest.TextTestRunner(stream=report, verbosity=2).run(suite)
    finally:
        sys.settrace(None)
        threading.settrace(None)

    files = {}
    for real, name in wanted.items():
        code_lines = executable_lines(Path(real))
        files[name] = {
            "lines": sorted(code_lines),
            "missing": sorted(code_lines - seen[name]),
        }
    out.write_text(json.dumps({
        "run": result.testsRun,
        "broken": [
            {"test": test.id(), "traceback": trace}
            for test, trace in result.failures + result.errors
        ],
        "skipped": [test.id() for test, _ in result.skipped],
        "report": report.getvalue(),
        "files": files,
    }), encoding="utf-8")


if __name__ == "__main__":
    main()
