# DES-000 — Baseline: AI first-response server script (existing)

- **Status:** recorded (existing feature, not part of this change)
- **Covers:** server scripts `ai1`, `aiEnv` on site `inquiries`

## Ladder (I5)

Rung: **server script**. Reason: the feature calls an external AI service (via the internal AI gateway, `patterns/ai-gateway/`); this cannot be done with standard settings, formulas or プロセス.

## Notes

- `aiEnv` holds environment settings only (`${env:AI_GATEWAY_URL}`), no secrets (I7). Uses `var` (D7).
- `ai1` references the response-history site as `${site:responses}` — the hard-coded SiteId found in the spike (D3) is resolved per environment by `pls pack`.
