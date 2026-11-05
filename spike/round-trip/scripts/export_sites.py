"""Export site configuration (read-only) → data/<env>/<label>/<siteId>.json + .normalized.json

Examples:
  python scripts/export_sites.py --config scripts/config.json --env local --label original
  python scripts/export_sites.py --config scripts/config.json --env local --label x --site-ids 101 102
"""
from __future__ import annotations

import argparse

from common import (DATA_DIR, api_body, env_settings, extract_site, load_config,
                    normalize, post, volatile_sets, write_json)


def export_one(cfg: dict, env: dict, site_id: int) -> dict:
    path = cfg["endpoints"]["get_site"].format(id=site_id)
    resp = post(env, path, api_body(cfg, env), write=False)
    return resp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--label", required=True, help="output folder name, e.g. original")
    ap.add_argument("--site-ids", nargs="*", type=int)
    args = ap.parse_args()

    cfg = load_config(args.config)
    env = env_settings(cfg, args.env)
    ids = args.site_ids or cfg["site_ids"]
    volatile, nested = volatile_sets(cfg)
    out_dir = DATA_DIR / args.env / args.label

    for sid in ids:
        resp = export_one(cfg, env, sid)
        write_json(out_dir / f"{sid}.json", resp)
        write_json(out_dir / f"{sid}.normalized.json", normalize(extract_site(resp), volatile, nested))
        print(f"✓ site {sid} → {out_dir}")


if __name__ == "__main__":
    main()
