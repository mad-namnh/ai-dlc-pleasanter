# Review — P3-3 refusals with next action

- **Reviewer:** `pls-x-reviewer`, model `sonnet`, effort `medium`; round 1 of 2; working tree against `5a689b1`.
- **Verdict:** accept — 0 Critical, 0 High, 0 Medium, 2 Low. Reviewer ran: Python 456 OK, node 15 pass.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| L1 | Low | The apply-path not-planned refusal had no direct test (only the message function and the package path) | Fixed: `ApplyRefusalTest` runs `pls apply` on an `applied` and an `applied-unverified` release: exit 2, next action in stderr, no `updatesite` sent |
| L2 | Low | A `TransportError` not caught by `_main` now ends in the generic exit-3 line | No change: type name and first line are shown; the wording points to the machine first, then to a defect; every command that talks to Pleasanter already catches `TransportError` in `http_cmd` |
