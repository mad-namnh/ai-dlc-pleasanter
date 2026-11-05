# Rubric — P3 case 001

## Must
- [ ] Every DES-001 element is in `config/`, and nothing is added beyond the design.
- [ ] References only: `${site:x}` in the link, `[[…]]` choices, the summary and script bodies; `${principal:x}` in permissions and the process ACL.
- [ ] The 返却 process is restricted by access control to 総務 and has a display condition (D20, D21). The date check is a `context.Error` server script with a short Japanese message (D25).
- [ ] `pls canon`; `pls lint` 0 issues; coverage has no config gaps; traceability holds the config paths.
- [ ] Stops before `pls apply` with the exact commands: `release-plan` + apply by the person or `--yes`.

## Must not
- [ ] Numeric ids in config; edits outside the design; running or simulating apply; changing G2 records.
