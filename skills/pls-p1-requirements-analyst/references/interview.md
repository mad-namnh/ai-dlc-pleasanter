# Interview mode — from a rough idea to confirmed answers

Use it when the input is an idea, not a specification (SKILL.md, "When the input is a rough idea"). You ask, the person answers, and only what the person said becomes a requirement. You do not design here.

## 1. Before the first question

1. Create the record `requirements/sources/YYYY-MM-DD-interview-<slug>.md` (form in section 6) and put the idea into it **verbatim**, with who gave it, their role and the date.
2. Read what already answers a question: `config/` and `requirements/index.md` (existing app). Never ask what the repository already says; ask the person to confirm it only when the idea seems to contradict it.
3. For each area of section 3, look up in `pls-kb-pleasanter` what Pleasanter offers. You ask in those terms (section 4).
4. Interview in **the language the person writes in**. The record keeps questions and answers in that language. Labels and messages meant for Pleasanter end users stay Japanese; `REQ-*.md` and `index.md` stay English, as always.

## 2. How to ask

- **Open questions first.** "How is this done today, step by step?", "What happens after a request is approved?" The person describes; you do not offer an answer.
- **Choices only to close a point** the person already raised, or to pick between ways that differ for the design: 2–4 options and always "something else". Never open a topic with a list of options.
- One topic per question. No leading questions ("you want a mail to the manager, right?"). No design words (column slot, プロセス, server script, Summary) unless the person used them.
- Ask about **cases**, not features: who does it, on what data, what must be true before, what happens when it is not.
- When an answer is vague ("as usual", "the manager decides"), ask once for an example before moving on.

## 3. What to cover, and in which order

Eight areas. Ask first what changes the design most: a wrong answer there changes the sites, the permission model or existing data, the others only a setting.

| Order | Area | What you need to know |
|---|---|---|
| 1 | Data and fields | what one record is; the fields people fill in or read; which are required; links to other records |
| 1 | Life cycle and statuses | the states a record passes through, who moves it, what ends it, what may never happen |
| 1 | Roles and permissions | who creates, changes, only reads, must not see; per record or per site |
| 2 | Existing data and migration | where the data lives today, how much, whether it must be carried over and by when |
| 2 | Notifications and reminders | who must learn what, when, how (mail, screen), and what must not be sent |
| 3 | Validation rules | what input is refused, what depends on another field |
| 3 | Lists and reports | which lists people open daily, filters, totals, exports |
| 4 | Volume and deadline | records per month, number of users, the date it must work, what can come later |

Skip an area only when the idea or the repository already answers it; say so in the summary. An area nobody could answer is an open question, not a gap you fill.

## 4. Ask from what Pleasanter can do

- Phrase a question around what the KB says Pleasanter offers for that area, so that the answer can be built.
- **The person asks for something the KB says Pleasanter cannot do** (an entry says so for the target version): tell the person, name the entry, record it as a **constraint** (`C<n>`) and ask what they need behind it ("what would that let you do?"). The need becomes the answer; the impossible form never becomes a requirement.
- **The KB says nothing** about it: it is neither a constraint nor a promise. Record the wish as the person said it and mark it `[unverified]`; it goes to the open questions for P2. Do not guess what Pleasanter does.

## 5. Your own proposals

You may propose when the person asks what you suggest, or to close a gap after an open question brought nothing.

- A proposal is recorded as `P<n>`, apart from the questions, with the person's response **verbatim** under it.
- Only an explicit acceptance in the person's words ("yes, do it that way", "OK with 3 days") makes a proposal a source for a requirement. Record a changed proposal as the person changed it.
- Silence, "maybe", "I'll check", "whatever you think" are **not** acceptance: the point becomes an open question with your proposal as its `[assumed]` default.
- Never count your own proposal as something the person asked for.

## 6. The record

One file per interview; it is the source of the requirements, so it is never tidied up.

```markdown
# Interview — <topic>

- **Person:** <name>, <role> · **Interviewer:** AI (pls-p1-requirements-analyst) · **Date:** YYYY-MM-DD · **Language:** <language>

## The idea (verbatim)

> <what the person first wrote>

## Round 1

### Q1
<the question as asked>

**A1** (<name>): <the answer, verbatim>

### P1 — proposal by the AI
<the proposal as made>

**Response** (<name>): <verbatim> → accepted | changed | rejected | not answered

### C1 — constraint (KB D<n>)
<what was asked for, what Pleasanter cannot do, what the person needs instead — their words>

## Summary for confirmation
<section 8>

**Confirmation** (<name>): <verbatim>
```

- Numbers run through the whole file (`Q1…`, `A1…`, `P1…`, `C1…`) and are never reused. `A<n>` answers `Q<n>`.
- Verbatim means verbatim: no corrected wording, no merged answers. A later correction is a new answer that names the one it corrects ("A12 corrects A4"); the old one stays.
- What the person says outside a question (a remark, a new wish) is recorded as an answer of its own with a note "unprompted".

## 7. Rounds

- **At most 3 rounds, 5–8 questions each.** Send a round as one message; number the questions. Never more than 8. A last round may be shorter when fewer points are open: do not pad it with questions you do not need.
- After each round: write the answers into the record, mark the areas of section 3 as covered / partly / open, and choose the next questions from what is still open in order 1 → 4.
- Stop before round 3 when every area is covered. After round 3 stop asking: what is still unclear becomes an open question with an `[assumed]` default — the usual P1 form.
- **Nobody answers** (no person in the session, or the person stops): do not answer for them. Record the questions as asked, mark them "not answered", and go on with section 9 — everything unanswered is an open question.

## 8. Summary and confirmation

After the last round, send a summary **in the person's language** and ask them to confirm or correct it:

- what the app is for, in two or three sentences of their words;
- per area of section 3: the confirmed points, each with its answer numbers (`A3, A7`);
- the proposals they accepted **before the summary** (`P2`) and the constraints (`C1`);
- what is still open, with the default you will assume — shown as open, not as agreed.

The summary holds nothing new: no proposal appears in it for the first time, and a proposal the person did not accept earlier is listed under "still open". **Confirming the summary accepts no proposal and settles no open point** — "yes, that is right" means the summary reports the interview correctly.

Record the summary and the response verbatim. A correction is applied as a new answer. No confirmation → the summary's points stay as the answers they came from; nothing gains weight from a summary nobody confirmed.
The confirmation says "you understood me". It is **not** G1: the requirements are approved only at the gate, on the REQ files (I4).

## 9. From the record to requirements

Then run the normal procedure of SKILL.md from step 2, with the record as the source:

- Every requirement names its source answers: `Source: sources/<file> — A3, A7` (or an accepted proposal: `P2 accepted`). Acceptance criteria use the person's own cases and words where they gave them.
- **No source answer → not a requirement.** What you think the app needs, a proposal that was not accepted, an answer you had to interpret: an open question with an `[assumed]` default.
- A derived requirement still follows the rules of step 4 and names the requirement and answer it derives from.
- A constraint (`C<n>`) is listed with the open questions as a constraint for P2, with its KB entry; a requirement is written for the need the person stated instead, if they stated one.
- `[unverified]` wishes go to the open questions: "P2 must verify …".
- The summary was in the person's language; the question list in `index.md` is written as step 6 says (Japanese, for the customer), each with its `[assumed]` default.
- Hand over for **G1** as always.
