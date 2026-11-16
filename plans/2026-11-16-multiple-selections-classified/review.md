# Review — multiple selections classified

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **M1:** `ChoicesControlType` made config-only, against WS2.3 as written; radio buttons ignore multiple selection and show a stored array as empty (HtmlFields.cs l.573-592, HtmlControls.cs l.589) → data-impacting, "not verified"; test.
- **L1:** ADR line and test claimed a new column holds no values (a slot may hold data with no `Columns[]` entry, D12) → claim and assertion removed; ADR says slot reuse is the slot ledger's concern.
- **L2:** explicit `false` added / removed flagged → only when `bool(before) != bool(after)`; test.
- **L3:** inventory row, HANDOFF line, ADR-0004 open question for the WS3b probe. P2 impact checklist not changed (skill text → eval; not needed for the classifier).
- **L4:** removal of any column attribute labelled "column definition removed" — pre-existing, errs on the safe side; left.
