"""`pls status`: where the project stands and the next command, read from the repository only (no network, no write).

It answers lifecycle section 1 ("Find where the project is") deterministically, from the files `pls` itself trusts:
the profile (Origin, Release target), the onboarding summary, REQ / DES front matter with `pls check p1|p2`, the gate
records under `gates/` and the release records under `releases/`. Each open item is a line with the phase, the item and
the next command; "Next" is the first of them, in this order: records that refuse every check, the profile and the
onboarding, releases left unfinished, then the work furthest along (a release before its design, a design before
its requirement), so work in flight is finished before new work starts.

Limit: a design counts as built on dev after any dev release applied after its G2 (a release does not name the designs
it ships); with two designs in flight the second may be shown at P4 early, and `pls check p3 --des` then reports it.

A gate is never named as passed unless its record says so; status suggests the `pls gate` command only for after the
person's decision (I4) and never writes anything.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pls_front_matter as FM
import pls_gate as GT
import pls_phase_check as PC
import pls_profile_records as PR

_TARGET = re.compile(r"^\|\s*Release target\s*\|\s*`?(dev|stg|prod)`?\s*\|", re.M)
# Release states after `apply` started writing (pls.OPEN_STATES, kept equal by a test) and what recovers each
# (docs/setup.md, "When a release does not end applied"). Any other state outside DONE / PENDING is handled the same
# way: a state status does not know is never taken for "nothing open".
READ_BACK = "export every site of the release (pls export), then pls mark-applied {r} --export <site>=<file> …"
RECOVERY = {"applying": READ_BACK, "uncertain": READ_BACK, "applied-unverified": READ_BACK,
            "recovery-required": "a person restores the sites the apply message named from releases/{r}/rollback-<site>.json "
                                 "in Pleasanter, then " + READ_BACK}
ROLLED_BACK = "every site was restored; fix the cause, then make a new release plan with a new id"
DONE = ("applied", "applied-differs")
PENDING = ("planned", "migrated")
GATE_CMD = {"G1": "pls gate G1 --approver <name> --item {x} --quote \"<their words>\"",
            "G2": "pls gate G2 --approver <name> --item {x} --quote \"<their words>\"",
            "G3": "pls gate G3 --approver <name> --env {env} --release <R> --item {x} --quote \"<their words>\"",
            "G4": "pls gate G4 --approver <name> --release {x} --quote \"<their words>\""}


def _open(rank: int, phase: str, item: str, state: str, next_: str) -> dict:
    return {"rank": rank, "phase": phase, "item": item, "state": state, "next": next_}


def _approved(root: Path, gate: str, **key) -> tuple[bool, dict | None]:
    g = GT.latest(root, gate, **key)
    return bool(g and g.get("decision") == "approved"), g


def _undecided(gate: str, x: str, g: dict | None, env: str = "<target>") -> tuple[str, str]:
    """State and next step of an item whose gate is not approved: never decided, or sent back."""
    if g:
        return (f"{gate}: {g['decision']} by {g.get('approver')} on {g.get('date')}",
                f"rework {x} as the approver asked, then ask {gate} again")
    return (f"awaiting {gate}", f"present {gate} (skill pls-x-lifecycle, references/gates.md); after the person decides: "
            + GATE_CMD[gate].format(x=x, env=env))


def _front(path: Path) -> dict:
    try:
        return FM.read(path.read_text(encoding="utf-8"))[0] or {}
    except (OSError, UnicodeDecodeError, FM.FrontMatterError):
        return {}                                  # `pls check p1|p2` names the problem; status reports that finding


def _releases(root: Path) -> dict[str, dict]:
    out = {}
    for p in sorted((root / "releases").glob("*/plan.json")) if (root / "releases").is_dir() else []:
        try:
            plan = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, ValueError):
            plan = {"status": "unreadable"}
        if isinstance(plan, dict) and plan.get("kind") != "adopt":          # an adoption is a baseline, not a release
            out[p.parent.name] = plan
    return out


def _when(value) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(value))
        return t if t.tzinfo else t.astimezone()
    except ValueError:
        return None


def _unfinished(rel: str, status) -> tuple[str, str]:
    return (f"status {status}", RECOVERY.get(status, "read releases/{r}/plan.json and the last `pls apply` output; recover "
                                             "before any other release (docs/setup.md, \"When a release does not end applied\")")
            .format(r=rel))


def _release_step(root: Path, rel: str, plan: dict | None, target: str) -> tuple[str, str] | None:
    """After G3 named the release: plan it, G4, apply. None when the release is done."""
    g4, g = _approved(root, "G4", release=rel)
    if plan is None:
        return ("G3 approved, not planned", f"pls release-plan --env {target} --release {rel} --export <site>=<export> … "
                "(skill pls-p5-release-manager)")
    status = plan.get("status")
    if status == "rolled-back":
        return ("status rolled-back", ROLLED_BACK)
    if status not in DONE + PENDING:
        return _unfinished(rel, status)
    if not g4:
        return _undecided("G4", rel, g)
    if status in PENDING:
        return (f"G4 approved, {status}", f"the person runs: python pls.py apply {rel}")
    return None


def collect(root: Path) -> dict:
    """Every open item and the next step. A gate record that cannot be read refuses every check: it is the only item."""
    items: list[dict] = []
    try:
        GT.load(root)
    except GT.GateError as ex:
        return {"items": [_open(0, "records", "gates/", str(ex), "a person repairs or removes the record")], "sandboxes": []}
    profile = PR.effective_profile_text(root)
    origin = GT.origin(root)
    m = _TARGET.search(profile)
    target = m.group(1) if m else "<target>"
    if origin is None:
        items.append(_open(1, "profile", "Origin", "not recorded", "ask the person whether the app already runs in "
                           "Pleasanter, then: pls profile set Origin new|existing --approver <name> --quote \"<their words>\""))
    elif GT.onboarding_missing(root):
        items.append(_open(1, "onboarding", "app", "no onboarding summary (ops/onboarding/*-summary.md)",
                           "skill pls-x-onboarding (read only), then pls-x-spec-recovery"))

    releases = _releases(root)
    latest_applied: dict[tuple, str] = {}
    for rel, plan in sorted(releases.items(), key=lambda kv: (str(kv[1].get("applied_at") or ""), kv[0])):
        if plan.get("status") in ("applied", "applied-differs"):
            for s in plan.get("sites") or []:
                latest_applied[(plan.get("env"), s)] = rel
    for rel, plan in releases.items():
        st = plan.get("status")
        later = any(o.get("env") == plan.get("env") and o_rel > rel for o_rel, o in releases.items())
        if st == "rolled-back":
            if not later:                           # a newer release of that environment replaced it
                items.append(_open(2, "release", rel, "status rolled-back", ROLLED_BACK))
        elif st not in DONE + PENDING:
            items.append(_open(2, "release", rel, *_unfinished(rel, st)))
        elif st == "applied-differs" and rel in latest_applied.values():
            items.append(_open(3, "P3", rel, "applied, live differs from the payload",
                               "fold the live values into config/ (pls canon or edit), commit, plan the next dev release"))
        elif st in PENDING and plan.get("env_role") == "dev":
            items.append(_open(3, "P3", rel, f"{st} on {plan.get('env')}", f"the person runs: python pls.py apply {rel} "
                               "(or under the recorded standing permission for dev)"))

    findings = {}
    for f in PC.p1(root) + PC.p2(root):
        findings.setdefault(f["item"], []).append(f["msg"])
    des_docs = PC._docs(root / "design" / "decisions", PC.DES_FILE)
    covered_reqs, cited_sources = set(), set()
    for did, path in des_docs:
        fm = _front(path)
        covered_reqs.update(str(x) for x in fm.get("reqs") or [] if isinstance(fm.get("reqs"), list))
        ok2, g2 = _approved(root, "G2", item=did)
        if not ok2:
            state, nxt = _undecided("G2", did, g2)
            if findings.get(did):
                state, nxt = f"{len(findings[did])} finding(s) of pls check p2", f"fix them: pls check p2 ({findings[did][0]})"
            items.append(_open(6, "P2", did, state, nxt))
            continue
        if (g2.get("bound_des") or {}).get(did) not in (None, GT.des_digest(root, did)):
            items.append(_open(6, "P2", did, "edited after its G2", "ask G2 again for the edited design"))
            continue
        ok3, g3 = _approved(root, "G3", item=did)
        if not ok3:
            since = g2["_t"]
            built = any(p.get("env_role") == "dev" and p.get("status") in ("applied", "applied-differs")
                        and (_when(p.get("applied_at")) or since) > since for p in releases.values())
            if g3:
                items.append(_open(5, "P4", did, *_undecided("G3", did, g3, target)))
            elif built:
                items.append(_open(5, "P4", did, "built on dev after G2, awaiting G3",
                                   f"verify (skill pls-p4-test-writer): pls coverage; pls check p3 --env {target} --des {did}; "
                                   "write releases/<R>/g3-verification.md; then present G3"))
            else:
                items.append(_open(5, "P3", did, "G2 approved, nothing applied on dev since",
                                   "build (skill pls-p3-config-builder): pls lint; then pls release-plan --env dev "
                                   "--release R-<date>-NN-dev --export <site>=<export> …"))
            continue
        for rel in g3.get("releases") or []:
            step = _release_step(root, rel, releases.get(rel), target)
            if step:
                items.append(_open(4, "P5", f"{did} / {rel}", *step))

    try:                                            # older projects link REQ → DES only in traceability.json
        trace = json.loads((root / "traceability.json").read_text(encoding="utf-8-sig"))
        covered_reqs.update(k for k, v in trace.items() if isinstance(v, dict) and v.get("design"))
    except (OSError, UnicodeDecodeError, ValueError, AttributeError):
        pass                                        # pls coverage / check p3 refuse a broken file themselves
    for rid, path in PC._docs(root / "requirements", PC.REQ_FILE):
        fm = _front(path)
        cited_sources.update(Path(str(s).split(" ")[0]).name for s in (fm.get("sources") or [])
                             if isinstance(fm.get("sources"), list))
        ok1, g1 = _approved(root, "G1", item=rid)
        if not ok1:
            state, nxt = _undecided("G1", rid, g1)
            if findings.get(rid):
                state, nxt = f"{len(findings[rid])} finding(s) of pls check p1", f"fix them: pls check p1 ({findings[rid][0]})"
            items.append(_open(7, "P1", rid, state, nxt))
        elif rid not in covered_reqs:
            items.append(_open(7, "P2", rid, "G1 approved, no DES names it",
                               "design it (skill pls-p2-solution-designer): design/decisions/DES-<n>-<slug>.md"))
    if not GT.onboarding_missing(root):
        for p in sorted((root / "requirements" / "sources").glob("*-pending-*.md")):
            if p.name not in cited_sources:
                items.append(_open(8, "P1", p.name, "change request saved before onboarding, no REQ cites it",
                                   "analyse it (skill pls-p1-requirements-analyst)"))
    sandboxes = []
    try:
        envs = json.loads((root / "environments.json").read_text(encoding="utf-8-sig")).get("envs") or {}
        sandboxes = sorted(n for n, e in envs.items() if isinstance(e, dict) and e.get("sandbox_of"))
    except (OSError, UnicodeDecodeError, ValueError, AttributeError):
        pass                                        # every other command refuses a broken environments.json itself
    items.sort(key=lambda x: x["rank"])
    return {"items": items, "sandboxes": sandboxes, "target": target}


def render(state: dict) -> str:
    items = state["items"]
    lines = []
    if not items:
        lines.append("Nothing open: every requirement is designed, released and approved.")
        lines.append("Next: P6 — pls drift on the released environment (skill pls-p6-maintenance-triage for an inquiry), "
                     "or a new change request → P1 (skill pls-p1-requirements-analyst)")
    else:
        lines.append(f"{len(items)} open item(s), in the order to take them:")
        groups: list[list[dict]] = []               # neighbours in the same phase and state share one line
        for x in items:
            if groups and (groups[-1][0]["phase"], groups[-1][0]["state"]) == (x["phase"], x["state"]):
                groups[-1].append(x)
            else:
                groups.append([x])
        for g in groups:
            name = g[0]["item"] if len(g) == 1 else f"{g[0]['item']} … {g[-1]['item']} ({len(g)})"
            lines.append(f"  {g[0]['phase']:<10} {name:<24} {g[0]['state']}")
        lines.append(f"Next: {items[0]['next']}")
    for s in state.get("sandboxes") or []:
        name = s[4:] if s.startswith("dev-") else s
        lines.append(f"Sandbox {s}: harvest your UI edits (pls harvest --env {s} --site <site>) and commit before merging; "
                     f"after merging the shared branch: pls sandbox sync --name {name} (ADR-0011)")
    return "\n".join(lines)
