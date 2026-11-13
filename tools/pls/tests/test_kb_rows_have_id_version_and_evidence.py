"""Every entry of the knowledge base can be traced (design review F1): each row of behaviours.md has an ID, says the
version it holds on — or that it is a design rule, source-derived, or that its version was not recorded — and every
entry with a probe says what that probe contained. The reference files say what their file-level claim rests on."""
import json
import re
import unittest
from pathlib import Path

KB = Path(__file__).resolve().parents[3] / "skills" / "pls-kb-pleasanter" / "references"
ID = re.compile(r"^D\d+[a-z]?$")
VERSION_OR_MARKER = re.compile(r"\b1\.5\.\d|design rule|source-derived|version not recorded", re.I)


def rows() -> list[tuple[str, str]]:
    """(ID cell, whole row) of every data row of the behaviours table."""
    out = []
    for line in (KB / "behaviours.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) > 1 and cells[0] not in ("ID", "---") and not set(cells[0]) <= {"-"}:
            out.append((cells[0], line))
    return out


class KbRowsTest(unittest.TestCase):
    def test_every_row_has_an_id(self):
        bad = [r[:80] for i, r in rows() if not ID.match(i)]
        self.assertEqual(bad, [], "rows of behaviours.md without an ID")

    def test_ids_are_unique(self):
        ids = [i for i, _ in rows()]
        self.assertEqual(sorted({i for i in ids if ids.count(i) > 1}), [])

    def test_every_row_says_its_version_or_what_it_is(self):
        bad = [i for i, r in rows() if not VERSION_OR_MARKER.search(r)]
        self.assertEqual(bad, [], "rows without a version, 'design rule', 'source-derived' or 'version not recorded'")

    def test_every_probed_entry_says_what_its_probe_contained(self):
        index = json.loads((KB / "probes" / "index.json").read_text(encoding="utf-8"))["entries"]
        by_id = dict(rows())
        bad = [e for e, v in index.items() if v.get("probes") and not all(
            w in by_id.get(e, "").lower() for w in ("probe contained", "not covered"))]
        self.assertEqual(bad, [], "probed entries without 'Probe contained: …' and 'Not covered: …'")

    def test_reference_files_state_their_evidence(self):
        for name in ("api.md", "schema.md", "skeletons.md"):
            head = "\n".join((KB / name).read_text(encoding="utf-8").splitlines()[:8])
            self.assertIn("Evidence:", head, f"{name}: first lines do not say what the file-level claim rests on")


if __name__ == "__main__":
    unittest.main()
