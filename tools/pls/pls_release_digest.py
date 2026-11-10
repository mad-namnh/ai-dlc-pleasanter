"""Content digest of a planned release, so a G4 approval covers exactly what is written.

A G4 record stores, per release, the digest of the release folder as it was when the person approved it:
plan.json (or bootstrap.json) without the fields that later commands fill in, plus every payload, rollback and
scheduled-script file the plan uses and every file of its migration folders (`migrate` sends their data). `apply` / `bootstrap` on stg recompute it and refuse on any difference, so a
payload, a target environment or a site id edited after G4 is never written (I4).

Mutable fields are a deny list on purpose: a field added later is covered by the digest until it is listed here,
so a new field can only cause a refusal (re-approve), never an unchecked write.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

# filled in after G4 by apply, mark-applied, migrate, jobs-verified, bootstrap and bind
PLAN_MUTABLE = {"status", "applied_at", "apply_started_at", "apply_finished_at", "post_apply_check", "readback",
                "checked_at", "migrations_run"}
JOBS_MUTABLE = {"verified"}
BOOTSTRAP_MUTABLE = {"status", "created", "created_at", "uncertain"}
JOBS_FOLDER = "scheduled-scripts"


class DigestError(Exception):
    pass


def release_file(root: Path, release: str) -> Path | None:
    """plan.json of a release, else bootstrap.json of a bootstrap id; None when the release is not planned."""
    rel = root / "releases" / release
    for name in ("plan.json", "bootstrap.json"):
        if (rel / name).exists():
            return rel / name
    return None


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _content(doc: dict, bootstrap: bool) -> dict:
    out = {k: v for k, v in doc.items() if k not in (BOOTSTRAP_MUTABLE if bootstrap else PLAN_MUTABLE)}
    if isinstance(out.get("jobs"), dict):
        out["jobs"] = {k: v for k, v in out["jobs"].items() if k not in JOBS_MUTABLE}
    return out


def digest(root: Path, release: str) -> dict:
    """{"env", "sha256"} of the release as planned now. Raises DigestError when it cannot be computed."""
    f = release_file(root, release)
    if f is None:
        raise DigestError(f"{release} has no plan.json or bootstrap.json — plan it before G4")
    try:
        doc = json.loads(f.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as ex:
        raise DigestError(f"{f.name} of {release} is not readable JSON ({ex})")
    if not isinstance(doc, dict):
        raise DigestError(f"{f.name} of {release} is not a JSON object")
    bootstrap = f.name == "bootstrap.json"
    files: dict[str, str] = {}
    if not bootstrap:
        names = {s.get("payload_file") for s in (doc.get("steps") or []) + (doc.get("rollback") or [])
                 if isinstance(s, dict)}
        for name in sorted(n for n in names if n):
            p = f.parent / name
            if p.parent != f.parent or not p.is_file():
                raise DigestError(f"{release}: {name} named in plan.json is missing")
            files[name] = _sha(p.read_bytes())
        jobs = f.parent / JOBS_FOLDER
        for p in sorted(jobs.rglob("*")) if jobs.is_dir() else []:
            if p.is_file():
                files[p.relative_to(f.parent).as_posix()] = _sha(p.read_bytes())
        migs = doc.get("migration")
        for mig in [migs] if isinstance(migs, str) else migs if isinstance(migs, list) else []:
            d = Path(mig) if Path(mig).is_absolute() else root / mig
            if not d.is_dir():
                raise DigestError(f"{release}: migration folder {mig} named in plan.json is missing")
            for p in sorted(d.rglob("*")):
                if p.is_file():
                    files[f"migration:{mig}/{p.relative_to(d).as_posix()}"] = _sha(p.read_bytes())
    body = json.dumps({"file": f.name, "content": _content(doc, bootstrap), "files": files},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"env": doc.get("env"), "sha256": _sha(body.encode("utf-8"))}


def check(root: Path, release: str, bound: dict | None) -> str | None:
    """Why the recorded binding does not cover the release as planned now; None when it does."""
    if not isinstance(bound, dict) or not bound.get("sha256"):
        return (f"the G4 record of {release} does not name its content (recorded before the release was planned, or "
                f"by an older pls) — after the person approves this plan, record G4 again")
    now = digest(root, release)
    if now["env"] != bound.get("env"):
        return f"{release} now targets {now['env']!r}, G4 approved it for {bound.get('env')!r}"
    if now["sha256"] != bound["sha256"]:
        return (f"{release} changed since G4 (plan, payload, rollback, scheduled-script or migration files) — show the person "
                f"the new plan; a new G4 is needed")
    return None
