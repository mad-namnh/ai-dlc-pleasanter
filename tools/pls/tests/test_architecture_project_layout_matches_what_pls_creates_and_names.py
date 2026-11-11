"""docs/architecture.md §3.2 (project repository layout) against what pls creates and names.

Three checks, each read from the code — the test holds no copy of the layout:

  A. every file and folder `pls init` creates in an empty folder is in the tree, at the same place;
  B. every name pls joins into a path with `/` (tools/pls/*.py, read with ast) is a name in the tree, or is listed
     in NOT_IN_A_PROJECT with the reason it is not part of a project repository;
  C. every name in the tree that has no varying part is created by `pls init`, or named in a text constant of the
     pls sources, or in a `code` span of a skill or of the project template (files a skill writes, not pls).

Not checked: the comments of the tree; where in the tree a name of check B sits; names with a varying part in
check C; paths pls builds without `/` (a text constant such as "gates/review", a glob pattern) in check B.

    python -m unittest discover -s tools/pls/tests -v
"""
import ast
import re
import sys
import tempfile
import unittest
from pathlib import Path

PLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLS_DIR))
import pls  # noqa: E402

FRAMEWORK = PLS_DIR.parents[1]
ARCHITECTURE = FRAMEWORK / "docs" / "architecture.md"

# Names pls joins into a path that is not inside a project repository. A new name in the sources must be added to
# §3.2 or listed here with its reason; nothing else is hand-kept in this test.
NOT_IN_A_PROJECT = {
    ".git": "git's own folder (branch name for the run log)",
    "HEAD": "git's own file",
    "commondir": "git's own file",
    "packed-refs": "git's own file",
    ".keep": "keeps an empty folder in git; not part of the layout",
    "templates": "framework repository: templates/project",
    "project": "framework repository: templates/project",
    "README.md": "framework repository: skills/README.md (skill versions)",
    "SKILL.md": "inside a skill folder",
    "pls-kb-pleasanter": "framework repository: the knowledge base skill",
    "references": "framework repository: inside the knowledge base skill",
    "behaviours.md": "framework repository: inside the knowledge base skill",
    "index.json": "framework repository: probe index of the knowledge base",
    "canonical-defaults.json": "framework repository: next to pls.py",
    "pls_package_verify.py": "framework repository: shipped inside a release package as verify.py",
    "pls_release_digest.py": "framework repository: shipped inside a release package",
    "manifest.json": "inside a release package (dist/*.zip), read by verify.py",
    "g4.json": "inside a release package (dist/*.zip), read by verify.py",
    "profiles": "machine profile of `pls setup`, under the user's home folder",
    "*.admin.key": "machine profile of `pls setup`, under the user's home folder",
    "dev.json": "machine profile of `pls setup`, under the user's home folder",
    "projects": "Claude Code transcripts, under the user's home folder (pls usage)",
    "subagents": "Claude Code transcripts, under the user's home folder (pls usage)",
    "*.jsonl": "a Claude Code transcript <session>.jsonl, under the user's home folder (pls usage); the run log "
               "<day>-<actor>.jsonl is in the tree",
}


def shape(name: str) -> str:
    """A name with every varying part (`<site>` in the document, `{site}` of an f-string) as one `*`."""
    return re.sub(r"\*+", "*", re.sub(r"<[^<>]*>", "*", name))


def layout_paths(text: str) -> list[str]:
    """Paths of the §3.2 tree, relative to the project root, folders without their trailing `/`."""
    lines = text.splitlines()
    first = [i for i, line in enumerate(lines) if line.startswith("### 3.2 ")]
    last = [i for i, line in enumerate(lines) if line.startswith("### 3.3 ")]
    if len(first) != 1 or len(last) != 1 or last[0] < first[0]:
        raise AssertionError("docs/architecture.md: expected one heading '### 3.2 ' followed by one heading '### 3.3 '")
    fences = [i for i in range(first[0], last[0]) if lines[i].startswith("```")]
    if len(fences) != 2:
        raise AssertionError(f"docs/architecture.md §3.2: expected one fenced block (the tree), found {len(fences) / 2:g}")
    paths, stack = [], []
    for line in lines[fences[0] + 2:fences[1]]:                    # the first line of the block is the root folder
        m = re.match(r"^((?:│  |   )*)[├└]─ (\S+)(?:\s+#.*)?$", line)
        if not m:
            raise AssertionError(f"docs/architecture.md §3.2: not a tree line with one name: {line!r}")
        depth, name = len(m.group(1)) // 3, m.group(2).rstrip("/")
        if "/" in name or depth > len(stack):
            raise AssertionError(f"docs/architecture.md §3.2: one name per line, nested under its folder: {line!r}")
        stack = stack[:depth] + [name]
        paths.append("/".join(stack))
    return paths


def created_by_init() -> set[str]:
    """Every file and folder `pls init` creates, without what an installed skill holds and the `.keep` files."""
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        pls.init_project(project, "demo", "dev", None)
        found = {f.relative_to(project).as_posix() for f in project.rglob("*")}
    return {p for p in found if not p.startswith(".claude/skills/") and not p.endswith("/.keep")}


def _sources():
    for path in sorted(PLS_DIR.glob("*.py")):
        yield ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def names_pls_joins_into_paths() -> set[str]:
    """Shapes of the text operands of every `/` in the pls sources (`root / "ops" / f"{day}.jsonl"` → ops, *.jsonl)."""
    names = set()
    for tree in _sources():
        for node in ast.walk(tree):
            if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
                continue
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant) and isinstance(side.value, str):
                    names.update(shape(part) for part in side.value.split("/") if part)
                elif isinstance(side, ast.JoinedStr):
                    text = "".join(v.value if isinstance(v, ast.Constant) else "*" for v in side.values)
                    names.update(shape(part) for part in text.split("/") if part)
    return names - {"*"}                                           # a name with no fixed part says nothing


def _words(text: str) -> set[str]:
    return {w.rstrip(".") for w in re.split(r"[\s/`'\"(),;:|]+", text)} - {""}


def names_in_pls_text_constants() -> set[str]:
    """Every word of every text constant of the pls sources, split at `/` and white space."""
    names = set()
    for tree in _sources():
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                names |= _words(node.value)
    return names


def names_in_skills_and_template() -> set[str]:
    """Every word of every `code` span of the skills and of the project template's CLAUDE.md."""
    names = set()
    for path in sorted((FRAMEWORK / "skills").rglob("*.md")) + [FRAMEWORK / "templates" / "project" / "CLAUDE.md"]:
        for span in re.findall(r"`([^`\n]+)`", path.read_text(encoding="utf-8")):
            names |= _words(span)
    return names


def missing_from_layout(text: str) -> dict[str, list[str]]:
    """Checks A and B: what exists and the tree does not show."""
    paths = layout_paths(text)
    shapes = {shape(p.rsplit("/", 1)[-1]) for p in paths}
    return {"created by pls init": sorted(created_by_init() - set(paths)),
            "joined into a path by pls": sorted(names_pls_joins_into_paths() - shapes - set(NOT_IN_A_PROJECT))}


def unknown_in_layout(text: str) -> list[str]:
    """Check C: paths of the tree whose name has no varying part and that nothing creates or names."""
    known = ({p.rsplit("/", 1)[-1] for p in created_by_init()} | names_in_pls_text_constants()
             | names_in_skills_and_template())
    return sorted(p for p in layout_paths(text)
                  if "<" not in p.rsplit("/", 1)[-1] and p.rsplit("/", 1)[-1] not in known)


NOTHING_MISSING = {"created by pls init": [], "joined into a path by pls": []}


class ProjectLayoutTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.text = ARCHITECTURE.read_text(encoding="utf-8")

    def test_the_sources_were_read(self):
        self.assertIn("design/slot-ledger.json", created_by_init())
        self.assertGreater(len(created_by_init()), 20)
        self.assertGreater(len(names_pls_joins_into_paths()), 60)
        self.assertIn("payload-*.json", names_pls_joins_into_paths())
        self.assertGreater(len(layout_paths(self.text)), 60)

    def test_layout_shows_what_pls_init_creates_and_every_path_name_of_pls(self):
        self.assertEqual(missing_from_layout(self.text), NOTHING_MISSING,
                         "docs/architecture.md §3.2 does not show something that exists in a project")

    def test_layout_names_nothing_that_nobody_creates_or_names(self):
        self.assertEqual(unknown_in_layout(self.text), [],
                         "docs/architecture.md §3.2 names something that pls, the skills and the template do not")

    def test_names_listed_as_not_in_a_project_are_still_in_the_sources(self):
        self.assertEqual(sorted(set(NOT_IN_A_PROJECT) - names_pls_joins_into_paths()), [],
                         "NOT_IN_A_PROJECT lists a name pls no longer joins into a path: remove it")

    def test_a_path_removed_from_the_layout_is_reported(self):
        def without(start: str) -> str:
            kept = [line for line in self.text.splitlines() if not line.startswith(start)]
            self.assertEqual(len(kept), len(self.text.splitlines()) - 1, start)
            return "\n".join(kept)
        self.assertEqual(missing_from_layout(without("├─ pls.py ")),
                         {"created by pls init": ["pls.py"], "joined into a path by pls": ["pls.py"]})
        self.assertEqual(missing_from_layout(without("│  ├─ sources/ ")),
                         {"created by pls init": ["requirements/sources"], "joined into a path by pls": []})
        self.assertEqual(missing_from_layout(without("│     ├─ apply-log.json ")),
                         {"created by pls init": [], "joined into a path by pls": ["apply-log.json"]})
        self.assertEqual(missing_from_layout(without("│     ├─ payload-<site>.json ")),
                         {"created by pls init": [], "joined into a path by pls": ["payload-*.json"]})

    def test_a_folder_moved_to_another_place_is_reported(self):
        moved = self.text.replace("│  ├─ sources/ ", "│  │  ├─ sources/ ")           # two levels below requirements/
        self.assertNotEqual(moved, self.text)
        with self.assertRaises(AssertionError):                                      # deeper than its parent allows
            layout_paths(moved)
        moved = self.text.replace("│  ├─ probes/ ", "│  │  ├─ probes/ ")             # now under design/decisions
        self.assertNotEqual(moved, self.text)
        self.assertEqual(missing_from_layout(moved)["created by pls init"], ["design/probes"])

    def test_a_name_nobody_creates_is_reported(self):
        added = self.text.replace("├─ traceability.json ", "├─ secrets.catalog.json\n├─ traceability.json ")
        self.assertEqual(unknown_in_layout(added), ["secrets.catalog.json"])
        added = self.text.replace("│  │  ├─ meta.json ", "│  │  ├─ meta.yaml\n│  │  ├─ meta.json ")
        self.assertEqual(unknown_in_layout(added), ["config/<site>/meta.yaml"])


if __name__ == "__main__":
    unittest.main()
