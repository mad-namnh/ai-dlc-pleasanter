# Rubric — case 001

## Must

- [ ] Source request saved verbatim under `requirements/sources/`.
- [ ] Event-driven requirement(s) for the escalation action, with acceptance criteria covering: escalation date-time is recorded, and whether an inquiry has been escalated is observable (a status or the recorded date-time — either interpretation is acceptable if the choice is a question with an `[assumed]` default).
- [ ] A requirement for **when** escalation is available (priority 高 and open) **and** an unwanted-behaviour clause (not offered otherwise / not twice).
- [ ] A requirement for notifying the サポート責任者 by mail; acceptance criteria flag that delivery is not automatically testable (or equivalent).
- [ ] At least one **derived** requirement or explicit impact item about existing elements that enumerate statuses (view 未完了 and/or notification #1 and/or the AI script status map) **if** the requirements imply a new status.
- [ ] Detects the interaction with notification #1 (mail to [Manager] on Status/ClassE change, condition = view 未完了): escalation must not cause a second, misleading mail to the サポート責任者 — raised as a requirement or a question. *(Added 2026-11-05: slice #1 missed this; both independent runs found it.)*
- [ ] Considers the 対応期限 reminder (condition = view 未完了): escalated inquiries keep or lose it — raised as a requirement or a question.
- [ ] Open questions in Japanese with explicit `[assumed]` defaults, covering at least: who may escalate; whether it can be repeated.
- [ ] Every requirement uses EARS form with exactly one "shall".
- [ ] `requirements/index.md` lists all requirements with status awaiting G1.

## Must not

- [ ] Mark any requirement as approved.
- [ ] Name implementation mechanisms (プロセス, server script, ClassX slots) inside requirement statements.
- [ ] Silently decide an ambiguous point without listing it as a question/assumption (an `[assumed]` with no question number counts as silent).
- [ ] A requirement statement with more than one `shall`.
- [ ] Derived requirements that add behaviour nobody asked for and no existing element needs (e.g. a new validation, an extra export) instead of raising it as a question.
