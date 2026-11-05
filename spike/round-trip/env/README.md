# Local Pleasanter 1.5.x (Docker + PostgreSQL) — OPTIONAL

> By default the spike runs on **MADLAB's internal dev Pleasanter** (the `dev` environment in the config). Use this folder only when a clean, resettable environment is needed.

Based on the official `implem/pleasanter` image. **Check the current Docker manual before running** — CodeDefiner commands changed in 1.4.6:

- Manual: https://pleasanter.org/ja/manual/getting-started-pleasanter-docker
- CodeDefiner changes: https://pleasanter.org/ja/manual/codedefiner-changed-steps

## Steps

1. `cp .env.example .env`, set passwords and **the exact 1.5.x patch used by the customer** in `PLEASANTER_VERSION`.
2. Start the database: `docker compose up -d db`
3. Run CodeDefiner once per the manual (initialize the DB, language `ja`, time zone `Asia/Tokyo`). The sample command is the `codedefiner` service in `compose.yaml`; **verify its arguments against the manual** before running:
   `docker compose run --rm codedefiner`
4. Start: `docker compose up -d pleasanter`
5. Open http://localhost:50001 — default login Administrator / pleasanter; **change the password immediately**.
6. Enable the API if needed (`Parameters/Api.json` → `Enabled: true`) and create an API key for a tenant-admin user.

## Notes

- Record the exact version used in the spike report.
- Full reset: `docker compose down -v` (also deletes the DB volume).
- Do not expose the port outside the local machine.
