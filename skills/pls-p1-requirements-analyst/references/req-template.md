---
id: REQ-NNN
status: awaiting G1
type: event-driven
sources: [sources/YYYY-MM-DD-<slug>.md]
acceptance: 3
open_questions: []
---
# REQ-NNN — <short title>

- **Status:** awaiting G1
- **Source:** `sources/YYYY-MM-DD-<slug>.md` (or "derived from REQ-xxx impact analysis: <reason>"; interview mode: `sources/YYYY-MM-DD-interview-<slug>.md — A3, A7` or `P2 accepted`)
- **Type (EARS):** ubiquitous | event-driven | state-driven | unwanted behaviour | optional | complex

## Requirement

<one EARS statement>

## Acceptance criteria

1. <observable result, testable via API or edit screen>
2. …
3. *(Not automatically testable: <why>; see open question Qn.)*

## Front matter (read by `pls check p1`)

- `id` = the file's id; `status` as in the Status line; `type` one of `ubiquitous`, `event-driven`, `state-driven`, `unwanted behaviour`, `optional`, `complex`.
- `sources`: each a file under `requirements/sources/` (`sources/…`, optionally followed by ` — A3, A7` for interview answers), or `derived from REQ-xxx` (another REQ of the project), or exactly `P2 accepted` / `drift accepted`.
- `acceptance`: the number of numbered acceptance criteria below. `open_questions`: the question ids (as in the index's questions table) this requirement waits on.
- The format is a small subset of YAML (`key: value`, `key: [a, b]`); `pls check p1` names any line it cannot read.
