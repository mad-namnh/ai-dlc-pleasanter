"""Read-back and diff must show every change a release makes or a person makes on live:

- list items that share a ColumnName / Name / Id (server scripts with the same name exist in real sites) never hide
  each other in a diff;
- the title and the permissions a payload writes are compared when a release is read back and in drift.
"""
import unittest

import pls

E = {"sites": {"a": {"id": 201, "title": "dev_A"}}, "principals": {"ops": "Group,374"}}
PAYLOAD = {"Title": "dev_A", "ReferenceType": "Results", "Body": "", "SiteSettings": {"X": 1},
           "InheritPermission": 201, "Permissions": ["Group,374,31"]}


def export(**over):
    d = {"SiteId": 201, "Title": "dev_A", "ReferenceType": "Results", "Body": "", "UpdatedTime": "t1",
         "SiteSettings": {"X": 1}, "InheritPermission": 201, "Permissions": ["Group,374,31"]}
    d.update(over)
    return {"Response": {"Data": d}}


def readback(exp, pl=PAYLOAD):
    want = pls.payload_model(pl, E, "a")
    return pls.flat_diff(pls.same_meta(pls.logical(exp, E), want), want)


class DuplicateKeysTest(unittest.TestCase):
    def scripts(self, first, last):
        return [{"Id": 1, "Name": "init", "Body": first}, {"Id": 2, "Name": "init", "Body": last}]

    def test_a_change_in_any_item_with_a_repeated_name_is_shown(self):
        base = self.scripts("a", "b")
        for changed in (self.scripts("A", "b"), self.scripts("a", "B")):
            diffs = pls.flat_diff(base, changed)
            self.assertEqual(len(diffs), 1, diffs)
            self.assertEqual(diffs[0]["kind"], "changed")

    def test_unique_names_keep_their_readable_paths(self):
        diffs = pls.flat_diff([{"ColumnName": "ClassA", "LabelText": "x"}], [{"ColumnName": "ClassA", "LabelText": "y"}])
        self.assertEqual(diffs[0]["path"], "[ClassA].LabelText")

    def test_an_extra_item_with_a_repeated_name_is_added_not_merged(self):
        diffs = pls.flat_diff([{"Name": "init", "Body": "a"}], [{"Name": "init", "Body": "a"}, {"Name": "init", "Body": "b"}])
        self.assertEqual([(d["path"], d["kind"]) for d in diffs], [("[init#2]", "added")])

    def test_a_real_name_equal_to_a_suffixed_key_hides_nothing(self):
        base = [{"Name": "init", "Body": "a"}, {"Name": "init", "Body": "b"}, {"Name": "init#2", "Body": "c"}]
        changed = [{"Name": "init", "Body": "a"}, {"Name": "init", "Body": "B"}, {"Name": "init#2", "Body": "c"}]
        self.assertEqual(len(pls.flat_diff(base, changed)), 1)

    def test_repeated_names_with_ids_show_a_reorder_or_removal_as_such(self):
        base = self.scripts("a", "b")
        self.assertEqual([d["kind"] for d in pls.flat_diff(base, base[::-1])], ["reordered"])
        self.assertEqual([(d["path"], d["kind"]) for d in pls.flat_diff(base, base[1:])], [("[init@1]", "removed")])


class ReadBackTitleAndPermissionsTest(unittest.TestCase):
    def test_live_equal_to_the_payload_reads_back_clean(self):
        self.assertEqual(readback(export()), [])

    def test_permissions_not_applied_are_a_difference(self):
        diffs = readback(export(Permissions=[]))
        self.assertTrue(any(d["path"].startswith("permissions") for d in diffs), diffs)

    def test_a_title_not_applied_is_a_difference(self):
        self.assertEqual([d["path"] for d in readback(export(Title="old"))], ["title"])

    def test_permissions_are_ignored_when_git_does_not_manage_them(self):
        pl = {k: v for k, v in PAYLOAD.items() if k not in ("InheritPermission", "Permissions")}
        self.assertEqual(readback(export(Permissions=["User,9,511"]), pl), [])

    def test_a_tree_from_git_has_no_title_so_release_planning_ignores_it(self):
        git = pls.logical(export(), E)
        git.pop("title")
        self.assertNotIn("title", pls.same_meta(pls.logical(export(Title="anything"), E), git))


if __name__ == "__main__":
    unittest.main()
