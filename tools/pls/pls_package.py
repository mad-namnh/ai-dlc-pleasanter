"""Release package for an environment the framework does not write itself (production, ADR-0003; J1/J2).

`pls package <release>` turns a G4-approved release into one immutable zip for the customer's operator:

    releases/<R>/plan.json, payload-*.json, rollback-*.json, scheduled-scripts/, diff reports, approvals
    migrations/<dir>/ (migration.json, dry-run.md — never backup/: business data, taken on the target)
    g4.json                 the G4 record that approved exactly this content
    manifest.json           release, env, release digest, G4 approver and words, sha256 of every other file
    verify.py + pls_release_digest.py   standard-library check the operator runs before anything is imported
    CHECKLIST.md            the operator's steps

The layout mirrors the project repository, so `verify.py` recomputes the release digest with the same code that
bound G4 (`pls_release_digest`) and compares it with the G4 record and the manifest. The zip is deterministic (fixed
timestamps, sorted entries): the same content always gives the same sha256.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

import pls_release_digest as RD

FORMAT = "pls-package/1"
HERE = Path(__file__).resolve().parent
VERIFIER = HERE / "pls_package_verify.py"
RELEASE_DOCS = ("diff-report.md", "diff-report.operator.md", "approvals.md")
FIXED_TIME = (2000, 1, 1, 0, 0, 0)


class PackageError(Exception):
    pass


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def contents(root: Path, release: str, plan: dict) -> dict[str, bytes]:
    """Archive path → bytes of every release and migration file the package carries (before manifest and tools)."""
    rel = root / "releases" / release
    out: dict[str, bytes] = {}

    def add(p: Path, arc: str):
        out[arc] = p.read_bytes()
    add(rel / "plan.json", f"releases/{release}/plan.json")
    names = {s.get("payload_file") for s in (plan.get("steps") or []) + (plan.get("rollback") or []) if isinstance(s, dict)}
    for name in sorted(n for n in names if n):
        add(rel / name, f"releases/{release}/{name}")
    jobs = rel / RD.JOBS_FOLDER
    for p in sorted(jobs.rglob("*")) if jobs.is_dir() else []:
        if p.is_file():
            add(p, f"releases/{release}/{p.relative_to(rel).as_posix()}")
    for name in RELEASE_DOCS + tuple(sorted(x.name for x in rel.glob("raw-diff-*.md"))):
        if (rel / name).is_file():
            add(rel / name, f"releases/{release}/{name}")
    migs = plan.get("migration")
    for mig in [migs] if isinstance(migs, str) else migs if isinstance(migs, list) else []:
        if Path(mig).is_absolute() or ".." in Path(mig).parts:
            raise PackageError(f"migration folder {mig} is not inside the project — plan it with a relative path")
        d = root / mig
        for p in sorted(d.rglob("*")):
            r_ = p.relative_to(d)
            if p.is_file() and r_.parts[0] != RD.BACKUP_FOLDER:
                add(p, f"{Path(mig).as_posix()}/{r_.as_posix()}")
    return out


def checklist(manifest: dict) -> str:
    m = manifest
    lines = [
        f"# Release package {m['release']} → {m['env']}",
        "",
        "Run every step yourself, inside your network. No AI agent and no MADLAB machine takes part (ADR-0003, I3).",
        "",
        "1. **Verify** before anything else: `python verify.py --env "
        f"{m['env']} --release {m['release']}` in the unzipped folder. It must end `VERIFIED`. A verifier inside a"
        " package can be changed with it: once you have a reviewed copy of `verify.py` and `pls_release_digest.py`, run"
        " your copy with `--dir <unzipped folder>`.",
        f"2. **Compare the release digest** it prints with the one your approver approved at G4 (`{m['digest']['sha256']}`,"
        " also in `approvals.md`). A different value means a different release: stop.",
        f"3. **Approval:** G4 by {m['g4']['approver']} at {m['g4']['at']}: 「{m['g4']['quote']}」 — confirm that this person"
        " is your approver and that they said it.",
        "4. **Backup** every site of the release (and, for a migration, every record of its site) on the target, as your"
        " procedure requires (`customer-responsibilities.md`).",
    ]
    if m["migrations"]:
        lines.append(f"5. **Migrations** first, in the release window: {', '.join(m['migrations'])} (ADR-0004 order).")
    lines += [
        f"{6 if m['migrations'] else 5}. **Apply** the sites in this order: {' → '.join(m['sites'])} — the method is the"
        " one agreed in ADR-0003 (pending: runner or manual import). On failure restore in reverse order from the"
        " `rollback-*.json` files.",
        f"{7 if m['migrations'] else 6}. **Manual steps:** {m['manual_step'] or 'none'}.",
        f"{8 if m['migrations'] else 7}. **Report back** the result (applied / rolled back / unknown) and an export of each"
        " site, so the release is recorded and drift can be checked.",
        "",
    ]
    return "\n".join(lines)


def build(root: Path, release: str, plan: dict, g4: dict, approvers: list[str]) -> tuple[Path, dict]:
    """Write dist/<release>-<env>.zip and return (path, manifest). The caller has checked G4 and the plan."""
    files = contents(root, release, plan)
    digest = RD.digest(root, release)
    g4_clean = {k: v for k, v in g4.items() if not k.startswith("_")}
    files["g4.json"] = (json.dumps(g4_clean, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    files["verify.py"] = VERIFIER.read_bytes()
    files["pls_release_digest.py"] = (HERE / "pls_release_digest.py").read_bytes()
    manifest = {
        "format": FORMAT, "release": release, "env": plan.get("env"), "env_role": plan.get("env_role"),
        "digest": digest, "sites": plan.get("sites") or [],
        "g4": {k: g4_clean.get(k) for k in ("approver", "at", "quote", "decision")}, "approvers": approvers,
        "migrations": [m for m in ([plan["migration"]] if isinstance(plan.get("migration"), str) else plan.get("migration") or [])],
        "manual_step": (plan.get("jobs") or {}).get("manual_step"),
    }
    files["CHECKLIST.md"] = checklist(manifest).encode("utf-8")
    manifest["files"] = {arc: _sha(b) for arc, b in sorted(files.items())}
    files["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for arc in sorted(files):
            info = zipfile.ZipInfo(arc, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[arc])
    out = root / "dist" / f"{release}-{plan.get('env')}.zip"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(buf.getvalue())
    return out, dict(manifest, zip_sha256=_sha(buf.getvalue()), zip=out.relative_to(root).as_posix(),
                     created_at=datetime.now().astimezone().isoformat(timespec="seconds"))   # outside the zip: it stays deterministic
