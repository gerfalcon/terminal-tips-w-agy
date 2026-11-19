"""Setup check for the workshop. Run it once, at the start.

    python3 doctor.py       (Cloud Shell, macOS, Linux)
    python doctor.py        (Windows)

It changes nothing. It only looks.
Python standard library only. Nothing to install.
"""
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ON_WINDOWS = sys.platform.startswith("win")

REPO_FILES = [
    "AGENTS.md", "check.py", "serve.py", "game/puzzle.py", "game/render.py", "game/puzzles.json",
    "static/app.js", "tests/test_render.py", "tools/run_tests.py", "tools/stop_hook.py",
    "tasks/levels.md", "tasks/leaderboard.md", "tasks/more-words.md",
]

AGY_INSTALL = (
    "irm https://antigravity.google/cli/install.ps1 | iex      (in PowerShell)"
    if ON_WINDOWS else
    "curl -fsSL https://antigravity.google/cli/install.sh | bash"
)


def run(command):
    """Run a command. Return (worked, first line of its output)."""
    try:
        done = subprocess.run(command, cwd=str(ROOT), stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False, ""
    text = done.stdout.decode("utf-8", errors="replace").strip()
    return done.returncode == 0, (text.splitlines()[0] if text else "")


def check_place():
    if os.environ.get("CLOUD_SHELL") == "true":
        return True, "running in Cloud Shell", []
    return True, "running on your own computer", []


def check_python():
    version = "{}.{}.{}".format(*sys.version_info[:3])
    if sys.version_info >= (3, 8):
        return True, f"Python {version}", []
    return False, f"Python {version} is too old", [
        "Install Python 3.8 or newer (3.12 is a good choice) from https://www.python.org/downloads/",
    ]


def check_git():
    git = shutil.which("git")
    if not git:
        return False, "git not found", [
            "Install Git from https://git-scm.com/downloads",
            "Then open a new terminal and run this script again.",
        ]
    _, version = run([git, "--version"])
    return True, version or "git found", []


def check_git_identity():
    git = shutil.which("git")
    if not git:
        return False, "git identity not checked (git is missing)", []
    has_name, name = run([git, "config", "user.name"])
    has_email, email = run([git, "config", "user.email"])
    if has_name and name and has_email and email:
        return True, f"git identity: {name} <{email}>", []
    return False, "git does not know your name and email yet", [
        "Without them, git refuses to commit. Run these two lines with your own details:",
        '  git config --global user.name "Your Name"',
        '  git config --global user.email "you@example.com"',
    ]


def check_repo():
    missing = [name for name in REPO_FILES if not (ROOT / name).exists()]
    if missing:
        return False, "some repo files are missing: " + ", ".join(missing), [
            "Download or clone the repo again.",
        ]
    git = shutil.which("git")
    has_commit = bool(git) and (ROOT / ".git").exists() and run([git, "rev-parse", "HEAD"])[0]
    if not has_commit:
        return False, "this folder is not a git repo with a first commit yet", [
            "You probably downloaded the ZIP. Run these three lines in this folder:",
            "  git init",
            "  git add -A",
            '  git commit -m "starting point"',
        ]
    return True, "repo files are here, and git has a first commit", []


def check_agy():
    agy = shutil.which("agy")
    if not agy:
        return False, "agy (Antigravity CLI) not found", [
            "Install it:",
            f"  {AGY_INSTALL}",
            "Then open a NEW terminal and run this script again.",
        ]
    worked, version = run([agy, "--version"])
    found = f"agy (Antigravity CLI) is installed: {version}" if worked and version else "agy (Antigravity CLI) is installed"
    return True, found, []


def check_port():
    port = int(os.environ.get("PORT", "8080"))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False, f"port {port} is busy", [
                "Maybe the game already runs in another terminal tab. Stop it with Ctrl+C,",
                f"or use another port: PORT={port + 1} python3 serve.py",
            ]
    return True, f"port {port} is free for the game", []


CHECKS = [check_place, check_python, check_git, check_git_identity, check_repo, check_agy, check_port]


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")  # never crash on an unusual character
    print("Workshop setup check")
    print()
    failures = 0
    for check in CHECKS:
        ok, message, help_lines = check()
        print(("[ok]   " if ok else "[FAIL] ") + message)
        for line in help_lines:
            print("       " + line)
        if not ok:
            failures += 1

    print("[note] Sign-in is not checked here. Start agy once and sign in with")
    print("       Google. If a work or university account fails, use a personal one.")
    print()
    if failures:
        print(f"{failures} thing(s) to fix. Fix the [FAIL] lines, then run this again.")
        return 1
    print("You are ready. On to the next step of the codelab.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
