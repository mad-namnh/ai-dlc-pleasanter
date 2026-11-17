"""Every SKILL.md frontmatter follows Anthropic's Agent Skills rules for `name` and `description`.

Skills under `skills/` are installed into project repositories (ADR-0022) and may be uploaded through the API or
claude.ai, which refuse a skill whose frontmatter breaks these rules: `name` at most 64 characters, lowercase letters,
digits and hyphens, no XML tags, not "anthropic" or "claude"; `description` not empty, at most 1024 characters, no XML
tags. Claude Code itself loads such a skill anyway, so nothing else would notice (P3 0.9 had `config/<site>/` in its
description). `name` also equals the folder name. Repository files are only read.
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL_FILES = sorted([*ROOT.glob("skills/*/SKILL.md"), *ROOT.glob(".claude/skills/*/SKILL.md")])

XML_TAG = re.compile(r"</?[A-Za-z][^<>]*>")
NAME_SHAPE = re.compile(r"[a-z0-9-]+")
RESERVED_WORDS = ("anthropic", "claude")


def frontmatter(path: Path) -> dict[str, str]:
    """Top-level `key: value` pairs of the leading `---` block; indented lines continue the previous value.

    Not a YAML parser: quotes and a folded-scalar `>` stay in the value. The framework's skills use plain one-line
    values; a quoted `name` therefore fails the name rules loudly rather than passing unchecked.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        match = re.match(r"([A-Za-z_][\w-]*):\s?(.*)$", line)
        if match and not line[0].isspace():
            key = match.group(1)
            fields[key] = match.group(2).strip()
        elif key is not None and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return {}  # no closing `---`: not a frontmatter block


def problems(path: Path, root: Path = ROOT) -> list[str]:
    """Every rule `path` breaks, each naming the file (relative to `root`) and the rule."""
    where = path.relative_to(root).as_posix()
    fields = frontmatter(path)
    if not fields:
        return [f"{where}: no frontmatter block (--- … ---)"]
    found = []
    name = fields.get("name", "")
    if name != path.parent.name:
        found.append(f"{where}: name {name!r} is not the folder name {path.parent.name!r}")
    if len(name) > 64:
        found.append(f"{where}: name longer than 64 characters")
    if not NAME_SHAPE.fullmatch(name):
        found.append(f"{where}: name {name!r} has characters other than lowercase letters, digits and hyphens")
    found += [f"{where}: name contains the reserved word {w!r}" for w in RESERVED_WORDS if w in name.lower()]
    found += [f"{where}: name contains the XML tag {tag!r}" for tag in XML_TAG.findall(name)]
    description = fields.get("description", "")
    if not description:
        found.append(f"{where}: description missing or empty")
    if len(description) > 1024:
        found.append(f"{where}: description has {len(description)} characters (at most 1024)")
    found += [f"{where}: description contains the XML tag {tag!r}" for tag in XML_TAG.findall(description)]
    return found


def problems_of(folder_name: str, fields: str) -> list[str]:
    """`problems` of a SKILL.md with these frontmatter lines, written to a temporary folder outside the repository."""
    root = Path(tempfile.mkdtemp())
    try:
        (root / folder_name).mkdir()
        path = root / folder_name / "SKILL.md"
        path.write_text(f"---\n{fields}---\n\n# body\n", encoding="utf-8")
        return problems(path, root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


class SkillFrontmatterTest(unittest.TestCase):
    def test_every_skill_frontmatter_follows_the_agent_skills_rules(self):
        self.assertGreaterEqual(len(SKILL_FILES), 12, "fewer SKILL.md files than the framework has")
        found = [p for path in SKILL_FILES for p in problems(path)]
        self.assertEqual(found, [], "SKILL.md frontmatter breaks the Agent Skills rules")

    def test_the_rules_catch_what_they_name(self):
        cases = {
            "description: Builds config/<site>/ files.": "XML tag '<site>'",
            "description: Ends a block </site> here.": "XML tag '</site>'",
            "description:": "description missing or empty",
            "description: " + "x" * 1025: "1025 characters",
        }
        for body, expected in cases.items():
            with self.subTest(body=body[:40]):
                found = problems_of("pls-x-probe", f"name: pls-x-probe\n{body}\n")
                self.assertTrue(any(expected in p for p in found), found)
        found = problems_of("pls-x-Claude", "name: pls-x-Claude\ndescription: Fine when a < b > c.\n")
        self.assertTrue(any("reserved word 'claude'" in p for p in found), found)
        self.assertTrue(any("other than lowercase" in p for p in found), found)
        self.assertFalse(any("XML tag" in p for p in found), found)
        self.assertEqual(problems_of("pls-x-probe", "name: pls-x-probe\ndescription: Fine.\n"), [])
        self.assertTrue(any("not the folder name" in p for p in problems_of("pls-x-a", "name: pls-x-b\ndescription: x\n")))


if __name__ == "__main__":
    unittest.main()
