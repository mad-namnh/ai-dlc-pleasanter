"""Round-trip site configuration on a dev/local Pleasanter and compare with the original.

Modes:
  create : create a new site from the exported configuration (under roundtrip_parent_id), export it, diff
  update : write the original configuration back onto the same site N times (--repeat), export after each, diff
           (write i vs original, and write i vs write i-1 to check idempotence)
           NOTE: run update mode only against copies inside the spike folder, never original sites.

Examples:
  python scripts/roundtrip.py --config scripts/config.json --env dev --mode create --label original
  python scripts/roundtrip.py --config scripts/config.json --env dev --mode update --label original --repeat 2
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from common import (DATA_DIR, api_body, confirm_write, diff, env_settings, extract_site,
                    load_config, normalize, post, read_json, top_area, volatile_sets, write_json)
from export_sites import export_one

# Site-level fields sent back on create/update. Confirmed in step 0 on 1.5.2.
SITE_FIELDS = ["Title", "Body", "ReferenceType", "SiteSettings"]


def find_new_id(resp: dict) -> int:
    for container in (resp, resp.get("Response") or {}, (resp.get("Response") or {}).get("Data") or {}):
        if isinstance(container, dict):
            for k in ("Id", "SiteId"):
                v = container.get(k)
                if isinstance(v, int) and v > 0:
                    return v
    raise RuntimeError(f"New SiteId not found in the response — check step 0: {str(resp)[:300]}")


def site_payload(site: dict) -> dict:
    return {k: site[k] for k in SITE_FIELDS if k in site}


def is_id_like(d: dict) -> bool:
    return d["kind"] == "changed" and isinstance(d["before"], int) and isinstance(d["after"], int)


def render_report(title: str, results: list[dict]) -> str:
    lines = [f"# {title}", "", "| Original site | Compared with | Differences | Likely ID references | Most-changed areas |",
             "|---|---|---|---|---|"]
    for r in results:
        areas = Counter(top_area(d["path"]) for d in r["diffs"]).most_common(3)
        ids = sum(1 for d in r["diffs"] if is_id_like(d))
        lines.append(f"| {r['site']} | {r['compare']} | {len(r['diffs'])} | {ids} | "
                     + ", ".join(f"`{a}` ({n})" for a, n in areas) + " |")
    lines += ["", "## Details (max 50 rows per pair)", ""]
    for r in results:
        lines += [f"### Site {r['site']} — {r['compare']}", ""]
        if not r["diffs"]:
            lines += ["No differences ✅", ""]
            continue
        lines += ["| Path | Kind | Before | After |", "|---|---|---|---|"]
        for d in r["diffs"][:50]:
            b, a = (str(d["before"])[:60], str(d["after"])[:60])
            tag = " 🔗" if is_id_like(d) else ""
            lines.append(f"| `{d['path']}`{tag} | {d['kind']} | {b} | {a} |")
        lines.append("")
    lines += ["🔗 = changed integer value, usually a SiteId/ID reference (expected to differ in create mode).", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--env", default="local")
    ap.add_argument("--mode", choices=["create", "update"], required=True)
    ap.add_argument("--label", required=True, help="folder of the original export, e.g. original")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--yes", action="store_true", help="skip retyping the host name (dev environments only)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    env = env_settings(cfg, args.env)
    confirm_write(env, args.yes)  # fail fast, before doing anything
    volatile, nested = volatile_sets(cfg)

    src_dir = DATA_DIR / args.env / args.label
    out_dir = DATA_DIR / args.env / f"roundtrip-{args.mode}"
    originals = sorted(p for p in src_dir.glob("*.json") if not p.name.endswith(".normalized.json"))
    if not originals:
        raise SystemExit(f"No exported files in {src_dir}. Run export_sites.py first.")

    results = []
    for raw_path in originals:
        sid = int(raw_path.stem)
        site = extract_site(read_json(raw_path))
        base_norm = normalize(site, volatile, nested)

        if args.mode == "create":
            parent = cfg["roundtrip_parent_id"]
            body = api_body(cfg, env, TenantId=env.get("tenant_id", 1), ParentId=parent,
                            InheritPermission=parent, **site_payload(site))
            resp = post(env, cfg["endpoints"]["create_site"].format(id=parent), body, write=True)
            new_id = find_new_id(resp)
            after = normalize(extract_site(export_one(cfg, env, new_id)), volatile, nested)
            write_json(out_dir / f"{sid}-as-{new_id}.normalized.json", after)
            results.append({"site": sid, "compare": f"new site {new_id} vs original", "diffs": diff(base_norm, after)})
            print(f"✓ {sid} → created {new_id}")

        else:
            prev = base_norm
            for i in range(1, args.repeat + 1):
                body = api_body(cfg, env, **site_payload(site))
                post(env, cfg["endpoints"]["update_site"].format(id=sid), body, write=True)
                cur = normalize(extract_site(export_one(cfg, env, sid)), volatile, nested)
                write_json(out_dir / f"{sid}-iter{i}.normalized.json", cur)
                results.append({"site": sid, "compare": f"write {i} vs original", "diffs": diff(base_norm, cur)})
                if i > 1:
                    results.append({"site": sid, "compare": f"write {i} vs write {i-1} (idempotence)",
                                    "diffs": diff(prev, cur)})
                prev = cur
                print(f"✓ {sid} updated ({i})")

    write_json(out_dir / "diffs.json", results)
    report = render_report(f"Round-trip ({args.mode})", results)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"Report: {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
