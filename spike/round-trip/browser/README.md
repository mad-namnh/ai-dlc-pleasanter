# Browser runner

Use this when the machine running the scripts cannot reach Pleasanter (proxy / internal network), or when you prefer not to issue an API key.
The Pleasanter API accepts the browser's logged-in session, so you only need to **log in manually** and run `roundtrip-browser.js` in the DevTools console (or via a browser automation tool).

- Writes only to copies inside the spike folder; never to original sites.
- `create`, `update` and `pkg` refuse until you run `spike.arm('dev', '<host name of the tab>')`. Do that only on a dev environment; any other role or host leaves them refusing.
- Returns only diffs with secrets masked (`sk-ant-...` → `[REDACTED]`).
- Normalize/diff logic is equivalent to `scripts/common.py`.

Spike round 1 (2026-11-05) was run with this runner (see `../report-20261105.md`).
