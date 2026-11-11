"""Every refusal of pls is run by at least one test of this suite, or is named in refusals_without_a_test.txt.

A refusal is a statement of tools/pls/*.py that stops a command: a `raise`, or a `print` / `return` whose text says
REFUSED, NOT marked or NOT VERIFIED. While the suite runs, this module records which lines of tools/pls/*.py are
executed (sys.monitoring, Python 3.12+). Its tests run last (the module name sorts after every other test module):

  - a refusal that no test ran and the list does not name fails the suite: write a test that reaches it;
  - a name in the list that a test now runs, or that is no longer in the sources, fails the suite: remove the line.

The list only gets shorter. An entry is the file, the function and the text of the statement — not a line number —
so moving code does not change it.

Not checked: that the test which reaches a refusal asserts anything about it (the review of the test does that);
refusals reached only in a child process (the launcher) count as not run; Python 3.10 and 3.11 (no sys.monitoring)
and a partial run (one file, `-k`) skip the comparison.

    python -m unittest discover -s tools/pls/tests -v
"""
import ast
import re
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PLS_DIR = TESTS_DIR.parent
LIST_FILE = TESTS_DIR / "refusals_without_a_test.txt"
SAYS_REFUSED = re.compile(r"\bREFUSED\b|NOT marked|NOT VERIFIED")

LINES_RUN: set[tuple[str, int]] = set()          # (file name, line) of tools/pls/*.py, filled while the suite runs
RECORDING = False


def _start_recording() -> bool:
    """Record every line of tools/pls/*.py that runs from now on. False when this Python cannot (before 3.12) or
    another tool already uses the coverage slot."""
    mon = getattr(sys, "monitoring", None)
    if mon is None or mon.get_tool(mon.COVERAGE_ID) is not None:
        return False
    pls_dir = str(PLS_DIR)

    def on_line(code, line):
        path = Path(code.co_filename)
        if str(path.parent) == pls_dir:
            LINES_RUN.add((path.name, line))
        return mon.DISABLE                        # one report per line is enough

    mon.use_tool_id(mon.COVERAGE_ID, "pls-refusal-lines")
    mon.register_callback(mon.COVERAGE_ID, mon.events.LINE, on_line)
    mon.set_events(mon.COVERAGE_ID, mon.events.LINE)
    return True


RECORDING = _start_recording()                   # at import: unittest imports every test module before the first test


def _is_refusal(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.Raise):
        return stmt.exc is not None              # a bare `raise` passes an error on; it is not a refusal of its own
    prints = isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and getattr(stmt.value.func, "id", "") == "print"
    if not (prints or isinstance(stmt, ast.Return)):
        return False
    return any(isinstance(n, ast.Constant) and isinstance(n.value, str) and SAYS_REFUSED.search(n.value)
               for n in ast.walk(stmt))


def refusals(sources: dict[str, str]) -> dict[str, tuple[str, int, int]]:
    """Refusal statements of the given sources: name → (file, first line, last line).

    The name is `file | function | statement text` (white space collapsed, cut at 140 characters); a second
    statement with the same name in the same function gets ` #2`.
    """
    found = {}
    for file, text in sorted(sources.items()):
        tree = ast.parse(text, filename=file)
        parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for stmt in sorted((s for s in ast.walk(tree) if isinstance(s, ast.stmt) and _is_refusal(s)),
                           key=lambda s: s.lineno):
            if getattr(parent[stmt], "lineno", None) == stmt.lineno:
                raise AssertionError(f"{file}:{stmt.lineno}: a refusal on the same line as its condition cannot be "
                                     f"told from the condition — put it on its own line")
            scope = parent[stmt]
            while not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
                scope = parent[scope]
            where = getattr(scope, "name", "<module>")
            words = " ".join((ast.get_source_segment(text, stmt) or "").split())[:140]
            name, n = f"{file} | {where} | {words}", 1
            while name in found:
                n += 1
                name = f"{file} | {where} | {words} #{n}"
            found[name] = (file, stmt.lineno, stmt.end_lineno or stmt.lineno)
    return found


def pls_sources() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(PLS_DIR.glob("*.py"))}


def listed(text: str) -> list[str]:
    """Names in the list file: one per line; empty lines and lines that start with `#` are not names."""
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def compare(found: dict[str, tuple[str, int, int]], lines_run: set[tuple[str, int]], names: list[str]) -> dict[str, list[str]]:
    """What must change: refusals no test ran that the list does not name, and names the list should not hold."""
    not_run = {name for name, (file, first, last) in found.items()
               if not any((file, line) in lines_run for line in range(first, last + 1))}
    return {"no test runs this refusal — write one (do not add it to the list)": sorted(not_run - set(names)),
            "listed, but a test runs it now — remove it from the list": sorted(set(names) & set(found) - not_run),
            "listed, but not in the sources (removed or reworded) — remove it from the list": sorted(set(names) - set(found)),
            "listed twice": sorted({n for n in names if names.count(n) > 1})}


NOTHING = {key: [] for key in compare({}, set(), [])}


def whole_suite_ran() -> str | None:
    """None when every test module of this folder was loaded without a filter; otherwise why the run is partial."""
    if any(arg == "-k" or arg.startswith("-k") for arg in sys.argv):
        return "tests were chosen with -k"
    loaded = {name.rsplit(".", 1)[-1] for name in sys.modules}
    missing = sorted(p.stem for p in TESTS_DIR.glob("test_*.py") if p.stem not in loaded)
    return f"not every test module was loaded (missing: {', '.join(missing[:3])}…)" if missing else None


class EveryRefusalHasATestOrIsListed(unittest.TestCase):
    maxDiff = None

    def test_the_sources_were_read(self):
        found = refusals(pls_sources())
        self.assertGreater(len(found), 250)
        self.assertTrue(any("| assert_writable |" in name and "REFUSED" in name for name in found), sorted(found)[:5])

    def test_every_refusal_is_run_by_a_test_or_listed(self):
        if not RECORDING:
            self.skipTest("needs sys.monitoring (Python 3.12+) with the coverage slot free")
        partial = whole_suite_ran()
        if partial:
            self.skipTest(f"only meaningful when the whole suite runs: {partial}")
        self.assertGreater(len(LINES_RUN), 3000, "the line recorder saw almost nothing — it is not recording")
        result = compare(refusals(pls_sources()), LINES_RUN, listed(LIST_FILE.read_text(encoding="utf-8")))
        if result != NOTHING:                                                # one name per line, ready to copy
            self.fail(f"refusals of pls and {LIST_FILE.name} differ:\n" + "\n".join(
                f"\n{what}:\n" + "\n".join(f"  {name}" for name in names) for what, names in result.items() if names))

    def test_the_list_holds_only_names_of_refusals(self):                  # also on Python 3.10: no recording needed
        found = refusals(pls_sources())
        names = listed(LIST_FILE.read_text(encoding="utf-8"))
        self.assertEqual(sorted(set(names) - set(found)), [])
        self.assertEqual(len(names), len(set(names)))

    def test_a_new_refusal_without_a_test_and_a_stale_list_line_are_reported(self):
        source = {"x.py": "def f(a):\n"
                          "    if a == 1:\n"
                          "        raise ValueError('one')\n"
                          "    if a == 2:\n"
                          "        print(\n"
                          "            'x: REFUSED - two')\n"
                          "        return 1\n"
                          "    if a == 3:\n"
                          "        return False, ['NOT marked: three']\n"
                          "    try:\n"
                          "        return int(a)\n"
                          "    except ValueError:\n"
                          "        raise\n"}
        found = refusals(source)
        one, two, three = ("x.py | f | raise ValueError('one')", "x.py | f | print( 'x: REFUSED - two')",
                           "x.py | f | return False, ['NOT marked: three']")
        self.assertEqual(sorted(found), sorted([one, two, three]))            # `return 1` and the bare raise are not
        ran_one_and_two = {("x.py", 3), ("x.py", 6)}                          # the print is reported at its last line
        self.assertEqual(compare(found, ran_one_and_two, [three]), NOTHING)
        self.assertEqual(compare(found, ran_one_and_two, []),
                         NOTHING | {"no test runs this refusal — write one (do not add it to the list)": [three]})
        self.assertEqual(compare(found, ran_one_and_two, [three, one]),
                         NOTHING | {"listed, but a test runs it now — remove it from the list": [one]})
        self.assertEqual(compare(found, ran_one_and_two, [three, "x.py | f | raise ValueError('gone')", three]),
                         NOTHING | {"listed, but not in the sources (removed or reworded) — remove it from the list":
                                    ["x.py | f | raise ValueError('gone')"], "listed twice": [three]})

    def test_two_refusals_with_the_same_text_get_different_names(self):
        found = refusals({"x.py": "def f(a):\n    if a:\n        raise ValueError('same')\n    raise ValueError('same')\n"})
        self.assertEqual(sorted(found), ["x.py | f | raise ValueError('same')", "x.py | f | raise ValueError('same') #2"])

    def test_a_refusal_on_the_line_of_its_condition_is_not_accepted(self):
        with self.assertRaises(AssertionError):
            refusals({"x.py": "def f(a):\n    if a: raise ValueError('one line')\n"})


if __name__ == "__main__":
    unittest.main()
