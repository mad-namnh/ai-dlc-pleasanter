"""Verify a pls release package before anything is imported (ADR-0003; review criterion J2).

Shipped inside every package as `verify.py`, next to `pls_release_digest.py`. Standard library only; no network, no
keys, no AI. Run it in the unzipped package folder:

    python verify.py --env prod --release R-20261110-01

It refuses (exit 1) when a file was added, removed or changed, when the target or release id differ from what the
operator expects, when the G4 record does not approve exactly this content, or when a site has no rollback file.
On success (exit 0) it prints the release digest, which the operator compares with the one the approver approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

FORMAT = "pls-package/1"
OWN = {"manifest.json"}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def problems(root: Path, env: str, release: str) -> tuple[list[str], dict]:
    """Every reason the package in `root` must not be used for `env` / `release`; empty when it may."""
    out: list[str] = []
    try:
        m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        return [f"manifest.json is missing or not JSON ({ex})"], {}
    if m.get("format") != FORMAT:
        out.append(f"unknown package format {m.get('format')!r}")
    if m.get("release") != release:
        out.append(f"the package is release {m.get('release')!r}, not {release!r}")
    if m.get("env") != env:
        out.append(f"the package targets {m.get('env')!r}, not {env!r}")
    listed = m.get("files") if isinstance(m.get("files"), dict) else {}
    present = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    for arc in sorted(present - set(listed) - OWN):
        out.append(f"{arc}: not part of the package (added after it was built)")
    for arc, sha in sorted(listed.items()):
        p = root / arc
        if not p.is_file():
            out.append(f"{arc}: missing")
        elif _sha(p) != sha:
            out.append(f"{arc}: changed since the package was built")
    sys.path.insert(0, str(root))
    try:
        import pls_release_digest as RD                    # the code that bound G4, shipped with the package
        now = RD.digest(root, release)
    except Exception as ex:                                # noqa: BLE001 - any failure here is a refusal
        return out + [f"the release digest cannot be computed ({ex})"], m
    finally:
        sys.path.pop(0)
    if now != m.get("digest"):
        out.append("the release content differs from the manifest's digest")
    try:
        g4 = json.loads((root / "g4.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        return out + [f"g4.json is missing or not JSON ({ex})"], m
    bound = (g4.get("bound") or {}).get(release) if isinstance(g4.get("bound"), dict) else None
    if g4.get("gate") != "G4" or g4.get("decision") != "approved" or release not in (g4.get("releases") or []):
        out.append("g4.json is not a G4 approval of this release")
    elif not isinstance(bound, dict) or bound.get("sha256") != now.get("sha256") or bound.get("env") != env:
        out.append("the G4 approval does not cover this content and target (approved a different release digest or env)")
    if g4.get("approver") not in (m.get("approvers") or []):
        out.append(f"the G4 approver {g4.get('approver')!r} is not a G4 approver of the project profile")
    try:
        plan = json.loads((root / "releases" / release / "plan.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        return out + [f"plan.json is missing or not JSON ({ex})"], m
    if plan.get("release") != release or plan.get("env") != env:
        out.append("plan.json names another release or target")
    back = {s.get("site") for s in plan.get("rollback") or [] if isinstance(s, dict) and s.get("payload_file")
            and (root / "releases" / release / s["payload_file"]).is_file()}
    for site in plan.get("sites") or []:
        if site not in back:
            out.append(f"{site}: no rollback file - there would be no way back")
    return out, m


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):        # a cp932 console must never stop the check on a character
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Verify a pls release package before import (standard library only).")
    ap.add_argument("--env", required=True, help="the environment you are about to change, e.g. prod")
    ap.add_argument("--release", required=True, help="the release id you were asked to apply")
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parent), help="unzipped package folder")
    a = ap.parse_args(argv)
    errs, m = problems(Path(a.dir), a.env, a.release)
    for e in errs:
        print(f"REFUSED: {e}")
    if errs:
        print(f"NOT VERIFIED - do not import this package ({len(errs)} problem(s)).")
        return 1
    g = m["g4"]
    print(f"release {m['release']} → {m['env']}: sites {' → '.join(m['sites'])}")
    print(f"release digest {m['digest']['sha256']} - compare it with the digest your approver approved")
    print(f"G4: {g['approver']} at {g['at']}: 「{g['quote']}」")
    if m.get("migrations"):
        print(f"migrations first: {', '.join(m['migrations'])}")
    if m.get("manual_step"):
        print(f"manual step: {m['manual_step']}")
    print("VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
