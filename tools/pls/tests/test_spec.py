"""As-is specification skeleton:  python -m unittest discover -s tools/pls/tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls_spec as SP  # noqa: E402

MODEL = {
    "meta": {"ReferenceType": "Issues"},
    "settings": {
        "Columns": [{"ColumnName": "Status", "ChoicesText": "1,下書き\n2,承認待ち"},
                    {"ColumnName": "ClassA", "LabelText": "企業", "ValidateRequired": True,
                     "ChoicesText": '[{"SiteId": ${site:kigyo}, "Lookups": []}]'},
                    {"ColumnName": "DateB", "LabelText": "応募締切日時"}],
        "EditorColumnHash": {"General": ["ClassA", "DateB"]},
        "Links": [{"ColumnName": "ClassA", "SiteId": "${site:kigyo}"}],
        "Processes": [{"Name": "提出①", "DisplayName": "提出", "CurrentStatus": 1, "ChangedStatus": 2,
                       "Groups": ["${principal:eigyo}"], "View": {"ColumnFilterHash": {"DateB": "x"}}}]},
    "scripts": {"ServerScripts": [{"Id": 1, "Name": "制限", "BeforeUpdate": True, "TryCatch": True,
                                   "Body": "const SITE_ID = ${site:kigyo};\nif ($p.ClassA) {}"}],
                "Scripts": [{"Id": 2, "Title": "画面", "All": True, "Body": "$p.set('DateB', 1);"}]},
    "permissions": {"entries": ["${principal:eigyo},15"], "inherit": "${site:anken}"},
}


class SkeletonTest(unittest.TestCase):
    def test_tables_come_from_the_configuration_and_only_narrative_is_left(self):
        text = SP.skeleton("anken", MODEL, {"anken": "案件一覧", "kigyo": "企業マスタ"})
        self.assertIn("# 画面設計書（現行）— 案件一覧", text)
        self.assertIn("| リンク先 | 「企業マスタ」 |", text)                       # itself left out
        self.assertIn("| ClassA | 企業 | 分類 | 必須 | ルックアップ: 「企業マスタ」 |", text)
        self.assertIn("| 提出 | 提出① | 下書き → 承認待ち | あり | 0 | 0 | ${principal:eigyo} |", text)
        self.assertIn("| サーバ | 制限 | BeforeUpdate | 2 | 企業 | 企業マスタ |", text)   # TryCatch is not a timing
        self.assertIn("| クライアント | 画面 | All | 1 | 応募締切日時 |", text)
        self.assertIn("- 継承元: 「案件一覧」", text)
        self.assertNotRegex(text, r"\b\d{3,}\b")                                    # no numeric ids
        self.assertEqual(SP.ai_markers(text), 5)                                     # overview, 2 scripts, 2 questions


if __name__ == "__main__":
    unittest.main()
