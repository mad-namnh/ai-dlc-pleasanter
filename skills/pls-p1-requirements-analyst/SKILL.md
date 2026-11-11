---
name: pls-p1-requirements-analyst
description: Phase P1 of AI-DLC for Pleasanter. Turns a customer request (meeting notes, email, ticket, drift accepted in operations) into testable EARS requirements with acceptance criteria, derived requirements and open questions for the customer, ready for gate G1. When the request is only a rough idea, interviews the person first and writes requirements only from their answers. Use whenever a new or changed requirement for a Pleasanter system arrives.
---

# pls-p1-requirements-analyst

**Goal:** customer intent → testable requirements in the project repository, ready for G1.
**You do not design or build here.** Mention design ideas only as assumptions to confirm.

## Inputs

- The request, verbatim (save it under `requirements/sources/YYYY-MM-DD-<slug>.md`).
- Current state: `config/` (unpacked sites), `requirements/index.md`, `design/` — to detect conflicts and impact.
- `pls-kb-pleasanter` — to know what Pleasanter can and cannot do.

## When the input is a rough idea (interview mode)

A specification, a mail or a ticket says who does what with which data: go to the procedure. An **idea** names a goal ("we want to manage X in Pleasanter") and leaves that out. Writing requirements from it would mean inventing them.

Use interview mode (`references/interview.md`) when one of these holds:
- the input does not say at least two of: what one record is and its fields; the states a record goes through; who may do what;
- you would have to settle core behaviour through `[assumed]` questions (more than about five) to write the first requirement;
- the person asks to be interviewed.

In interview mode you ask in at most 3 rounds, keep the questions and answers verbatim in `requirements/sources/YYYY-MM-DD-interview-<slug>.md`, get a summary confirmed, and then run the procedure below from step 2 with that record as the source. **A requirement needs a source answer (a derived requirement: the requirement and answer it derives from); without one it is a question.** Do not interview when the input is already a specification: use the open questions instead.

## Procedure

1. **Save the source** verbatim. Note who asked and when. Never paraphrase it away.
2. **Read the current configuration** of the sites involved (`config/<site>/site.json`, scripts). List the columns, statuses, views, notifications and scripts the request touches.
   For every notification, reminder, aggregation and process, record **what decides when it acts**, not only who receives it: the columns it watches, the view it uses as its condition (a notification's `BeforeCondition` / `AfterCondition` hold a view id — KB `schema.md`; a reminder may carry a condition too — its field and meaning are not in the KB, so read the exported `site.json`, compare it with the site's views, and record what you find as unverified) and a process's own filter (`View.ColumnFilterHash`). An element whose condition is a view takes over that view's filter — if the view filters on status, the element depends on status although its own settings never name one.
   For every "add / record / show X" in the request, check whether an **existing** column, choice or feature already holds or does X (compare labels, types and the data actually present in exports). If one does, do not write a requirement for a new element: write the requirement against the existing one and raise the overlap as a question with an `[assumed]` default (e.g. on a loan site asked to "record the extended due date": 「既存の『返却予定日』を延長後の期限として更新してよいですか？」).
3. **Extract requirements** as EARS statements (see `references/ears.md`). One behaviour per requirement, so **exactly one `shall`** in the statement. "Refuse X and show message Y" is two behaviours: keep the refusal as the requirement and put the message in the acceptance criteria (or split into two requirements).
4. **Derive hidden requirements** from impact on existing behaviour. Typical triggers:
   - a new status — or an open question whose answer could add one → every view that filters on status, every notification, reminder or process whose condition is such a view (step 2), aggregations by status, and scripts that enumerate statuses. When the status is only possible (an open question), name these elements in the impact analysis so the answer at G1 shows its whole impact;
   - a new column → grid, filters, editor layout, exports;
   - a new action → who may do it, can it repeat, what if conditions are not met.
   Mark them `(derived)` and state the source of the derivation.
   **New app (nothing runs yet):** there is no existing behaviour to protect, so derived requirements come only from the impact of one requested behaviour on another requested one (e.g. a new status that a requested view must still show). Everything else the app "obviously needs" is a question with an `[assumed]` default.
   Derived requirements **protect existing behaviour** from the impact of the change (views, notifications, reminders, aggregations, scripts). Behaviour the customer did not ask for and that no existing element needs (a new validation, an extra export, a new message) is **not** a requirement: raise it as a question with an `[assumed]` default, so G1 decides whether it enters scope.
5. **Write acceptance criteria** for each requirement: observable, numbered, testable through the API or the edit screen. If a criterion cannot be tested automatically (e.g. mail delivery), say so explicitly.
6. **List open questions** for the customer in **Japanese** (お客様への確認事項), each with the assumption you will use if unanswered, marked `[assumed]`.
7. **Update `requirements/index.md`** (ID, title, EARS type, status `awaiting G1`) and the questions table.
8. **Self-check** with the checklist below, then hand over for **G1**. Do not mark anything approved yourself (I4).

## Outputs (project repository)

```
requirements/sources/YYYY-MM-DD-<slug>.md
requirements/sources/YYYY-MM-DD-interview-<slug>.md   # interview mode: questions and answers verbatim (references/interview.md)
requirements/REQ-NNN-<slug>.md        # one per requirement — template in references/req-template.md
requirements/index.md                 # table + open questions
```

IDs are sequential across the project (`REQ-001`, `REQ-002`, …) and never reused.

## Checklist before G1

- [ ] Every requirement is a single EARS statement with a named trigger/state and a system response — count the `shall`s in each `## Requirement` section: exactly one.
- [ ] Every requirement has ≥ 1 acceptance criterion; untestable ones are flagged.
- [ ] Impact on existing statuses, views, notifications, reminders, scripts and permissions was checked — each element by its condition (watched columns, condition view), not only by its recipient; derived requirements recorded.
- [ ] No requirement asks for a new element where an existing column or feature already covers it (overlaps are questions).
- [ ] Ambiguities are questions with explicit assumptions, not silent choices. Every `[assumed]` in a REQ file points to a question number in `index.md`.
- [ ] No derived requirement adds behaviour beyond the request that no existing element needs (those are questions).
- [ ] Customer-facing text (questions, labels) is in Japanese; the rest of the document is English.
- [ ] Nothing in the requirements depends on a Pleasanter behaviour you have not verified (`pls-kb-pleasanter`). Interview mode: what the person asked for and the KB does not cover is a requirement marked `[unverified]` and listed for P2 to verify (`references/interview.md` sections 4 and 9), never dropped and never promised.
- [ ] Interview mode: every requirement names the answers it comes from (`A<n>`, or `P<n> accepted`; a derived requirement names the requirement and answer it derives from); a proposal of yours that the person did not accept in their own words is a question, not a requirement; the record holds the questions, answers, proposals and the confirmation verbatim.

## Example (illustrative — not a template to copy)

Request on an equipment-loan site: 「返却期限を過ぎた貸出は、総務がまとめて督促できるようにしたい。」
→ REQ-a (event-driven: when 総務 executes the reminder, the system shall …), REQ-b (state-driven + unwanted: while a loan is overdue and not returned …; if it is returned, then … not offered), REQ-c (derived: a new 督促済 status must still appear in the 貸出中 view and in every notification that watches status), questions such as 「督促は何回まで行いますか？」 with `[assumed]` defaults.
Your output depends on *this* request and *this* configuration — derive it, do not pattern-match the example.
