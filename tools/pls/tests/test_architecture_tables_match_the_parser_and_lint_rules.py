"""docs/architecture.md §7.1 (command table) and §7.2 (lint rule catalogue) name exactly what pls has.

The sources of truth are the argparse parser of pls.py and the rule codes of the issues `pls lint` builds; the
document is the side that is corrected. Sub-actions of a command (`skills check|sync`, `profile set`) and the
Phase / Purpose / Status text of a row are not checked.

    python -m unittest discover -s tools/pls/tests -v
"""
import argparse
import ast
import re
import sys
import unittest
from pathlib import Path

PLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLS_DIR))
import pls  # noqa: E402

ARCHITECTURE = PLS_DIR.parents[1] / "docs" / "architecture.md"


def section(text: str, start: str, end: str) -> str:
    """The lines from the heading that starts with `start` up to the heading that starts with `end`."""
    lines = text.splitlines()
    first = [i for i, line in enumerate(lines) if line.startswith(start)]
    last = [i for i, line in enumerate(lines) if line.startswith(end)]
    if len(first) != 1 or len(last) != 1 or last[0] < first[0]:
        raise AssertionError(f"docs/architecture.md: expected one heading '{start}' followed by one heading '{end}'")
    return "\n".join(lines[first[0] + 1:last[0]])


def first_cells(table_lines: list[str]) -> list[str]:
    """First cell of every body row. A cell ends at ' | ', so `check|sync` inside a cell stays whole."""
    return [line[1:].split(" | ")[0].strip() for line in table_lines[2:]]


def tables(section_text: str) -> list[list[str]]:
    """Every markdown table of a section, as its lines (header, separator, body rows)."""
    found, current = [], []
    for line in section_text.splitlines() + [""]:
        if line.startswith("|"):
            current.append(line)
        elif current:
            found.append(current)
            current = []
    return found


def documented_commands(text: str) -> set[str]:
    """Commands named in the first column of the §7.1 table: the first word of every `code` span, without `pls`."""
    found = tables(section(text, "### 7.1 ", "### 7.2 "))
    if len(found) != 1:
        raise AssertionError(f"docs/architecture.md §7.1: expected one table (the commands), found {len(found)}")
    names = set()
    for cell in first_cells(found[0]):
        spans = re.findall(r"`([^`]+)`", cell)
        if not spans:
            raise AssertionError(f"docs/architecture.md §7.1: no command in `code` in the first cell {cell!r}")
        for span in spans:
            words = span.split()
            names.add(words[1] if words[0] == "pls" and len(words) > 1 else words[0])
    return names


def parser_commands() -> set[str]:
    """Commands the parser of pls accepts."""
    subparsers = [a for a in pls.build_parser()._actions if isinstance(a, argparse._SubParsersAction)]
    if len(subparsers) != 1:
        raise AssertionError(f"pls.build_parser(): expected one set of commands, found {len(subparsers)}")
    return set(subparsers[0].choices)


def documented_lint_rules(text: str) -> set[str]:
    """Rules of the lint catalogue: the first table of §7.2. Later tables list checks that are not lint output."""
    found = tables(section(text, "### 7.2 ", "### 7.3 "))
    if not found:
        raise AssertionError("docs/architecture.md §7.2: no table")
    return set(first_cells(found[0]))


def emitted_lint_rules() -> set[str]:
    """Rule codes of the issues pls can report: the "rule" value of every issue dict built in tools/pls/*.py.

    A value that is not a literal must be a parameter of the function that builds the dict (a local helper such as
    `add(rule, msg)`); the codes are then the literals its calls pass. Anything else cannot be read from the source
    and fails the test, so a rule cannot be added in a form this check does not see.
    """
    rules, unreadable = set(), []
    for path in sorted(PLS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if not (isinstance(key, ast.Constant) and key.value == "rule"):
                    continue
                where = f"{path.name}:{node.lineno}"
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    rules.add(value.value)
                    continue
                helper = parents.get(node)
                while helper is not None and not isinstance(helper, ast.FunctionDef):
                    helper = parents.get(helper)
                params = [a.arg for a in helper.args.args] if helper is not None else []
                if not isinstance(value, ast.Name) or value.id not in params:
                    unreadable.append(f"{where}: the rule is neither a literal nor a parameter of its function")
                    continue
                position = params.index(value.id)
                calls = [c for c in ast.walk(tree) if isinstance(c, ast.Call)
                         and isinstance(c.func, ast.Name) and c.func.id == helper.name]
                if not calls:
                    unreadable.append(f"{where}: helper {helper.name}() is never called by name")
                for call in calls:
                    arg = call.args[position] if position < len(call.args) else next(
                        (k.value for k in call.keywords if k.arg == value.id), None)
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        rules.add(arg.value)
                    else:
                        unreadable.append(f"{path.name}:{call.lineno}: {helper.name}() is called without a literal rule")
    if unreadable:
        raise AssertionError("lint rule codes that cannot be read from the source:\n  " + "\n  ".join(unreadable))
    return rules


def differences(documented: set[str], actual: set[str]) -> dict[str, list[str]]:
    """What the document names and pls does not have, and what pls has and the document does not name."""
    return {"only in docs/architecture.md": sorted(documented - actual), "only in pls": sorted(actual - documented)}


NOTHING = {"only in docs/architecture.md": [], "only in pls": []}


class ArchitectureTablesTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.text = ARCHITECTURE.read_text(encoding="utf-8")

    def test_command_table_names_exactly_the_commands_of_the_parser(self):
        commands = parser_commands()
        self.assertGreater(len(commands), 30)                      # the parser was read, not an empty set
        self.assertEqual(differences(documented_commands(self.text), commands), NOTHING,
                         "docs/architecture.md §7.1 and the parser of tools/pls/pls.py name different commands")

    def test_lint_catalogue_names_exactly_the_rules_lint_can_report(self):
        rules = emitted_lint_rules()
        self.assertGreater(len(rules), 15)                         # the sources were read, not an empty set
        for rule in rules:
            self.assertRegex(rule, r"^L-[A-Z]+-\d{2}$")
        self.assertEqual(differences(documented_lint_rules(self.text), rules), NOTHING,
                         "docs/architecture.md §7.2 (first table) and the rules `pls lint` can report differ")

    def test_a_command_added_to_or_removed_from_the_table_is_reported(self):
        added = self.text.replace("| `pls canon` |", "| `pls no-such-command` | P3 | x | x |\n| `pls canon` |")
        self.assertEqual(differences(documented_commands(added), parser_commands()),
                         {"only in docs/architecture.md": ["no-such-command"], "only in pls": []})
        removed = "\n".join(line for line in self.text.splitlines() if not line.startswith("| `pls canon` |"))
        self.assertEqual(differences(documented_commands(removed), parser_commands()),
                         {"only in docs/architecture.md": [], "only in pls": ["canon"]})
        second_name = self.text.replace("| `pls canon` |", "| `pls canon` / `deploy` |")
        self.assertEqual(differences(documented_commands(second_name), parser_commands()),
                         {"only in docs/architecture.md": ["deploy"], "only in pls": []})

    def test_a_rule_added_to_or_removed_from_the_catalogue_is_reported(self):
        added = self.text.replace("| L-CAN-01 |", "| L-NONE-99 | x | x |\n| L-CAN-01 |")
        self.assertEqual(differences(documented_lint_rules(added), emitted_lint_rules()),
                         {"only in docs/architecture.md": ["L-NONE-99"], "only in pls": []})
        removed = "\n".join(line for line in self.text.splitlines() if not line.startswith("| L-CAN-01 |"))
        self.assertEqual(differences(documented_lint_rules(removed), emitted_lint_rules()),
                         {"only in docs/architecture.md": [], "only in pls": ["L-CAN-01"]})


if __name__ == "__main__":
    unittest.main()
