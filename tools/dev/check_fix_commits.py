"""Report `fix` commits of the framework that change pls without changing a test (design review H3, I9).

Rule (HANDOFF.md, "How we work"): a commit whose subject starts with `fix` and that changes a file under tools/pls/
outside tools/pls/tests/ also changes a file under tools/pls/tests/ — the regression test that fails on its parent.

This script checks only that a test file changed. That the test fails on the parent commit is shown by running it
there (a temporary git worktree), as before; a script cannot tell which test belongs to which fix.

    python tools/dev/check_fix_commits.py                 # commits after the start commit of the rule, up to HEAD
    python tools/dev/check_fix_commits.py --since <rev>   # another start
Exit code 1 when a commit is reported, 2 when git cannot be read. Read-only: runs `git log` and nothing else.
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RULE_SINCE = "151d4d9"          # the rule holds for commits after this one; older fix commits are listed in the review (H3)
CODE, TESTS = "tools/pls/", "tools/pls/tests/"


class GitError(Exception):
    pass


def _git(repo: Path, *args: str) -> str:
    try:
        res = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError as ex:
        raise GitError(f"git cannot be started: {ex}") from ex
    if res.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {res.stderr.strip()[:300]}")
    return res.stdout


def fix_commits_without_a_test(repo: Path, since: str) -> list[tuple[str, str]]:
    """(short hash, subject) of every commit in since..HEAD that is a fix of pls code and changes no pls test."""
    out = _git(repo, "log", "--no-merges", "--format=%x00%h%x09%s", "--name-only", f"{since}..HEAD")
    found = []
    for block in out.split("\x00")[1:]:
        head, *files = [line for line in block.splitlines() if line.strip()]
        short, subject = head.split("\t", 1)
        code = [f for f in files if f.startswith(CODE) and not f.startswith(TESTS)]
        if subject.lower().startswith("fix") and code and not any(f.startswith(TESTS) for f in files):
            found.append((short, subject))
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="fix commits that change tools/pls without changing a test")
    ap.add_argument("--since", default=RULE_SINCE, help=f"check the commits after this one (default {RULE_SINCE})")
    a = ap.parse_args(argv)
    try:
        found = fix_commits_without_a_test(REPO, a.since)
    except GitError as ex:
        print(f"check_fix_commits: {ex}", file=sys.stderr)
        return 2
    for short, subject in found:
        print(f"{short}  {subject}")
    print(f"{len(found)} fix commit(s) after {a.since} change tools/pls without a test"
          + (": add the regression test that fails on the parent commit" if found else ""))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
