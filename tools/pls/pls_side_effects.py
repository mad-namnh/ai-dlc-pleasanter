"""Side effects of configuration outside production: mail and scheduled jobs (ADR-0010).

Notifications and reminders are configuration that *runs*: a notification fires when a record changes,
a reminder fires on a schedule. On a non-production environment they can mail real people. Each
environment therefore declares what its side effects do, and `pls` refuses risky actions until a
person has stated that the environment is safe.

environments.json:
    envs.<env>.side_effects = {"mail": "unknown|sink|disabled|live", "jobs": "unknown|disabled|live"}
Missing values mean "unknown". Only a person sets them; agents never change them to get past a refusal.

Jobs are scheduled server scripts (ADR-0012): tenant settings with no API, kept in git under
config/_tenant/scheduled-scripts/ (<name>.js + _index.json) and deployed by hand. The tool cannot see the tenant,
so "the project has jobs" means "the project declares them in git".

Stdlib only; pls.py wires these into lint, release-plan, apply, test and http-check.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

from pls_adopt import SAFE_NAME

MAIL_STATES = ("unknown", "sink", "disabled", "live")
JOB_STATES = ("unknown", "disabled", "live")
MAIL_SAFE = ("sink", "disabled")          # a test or release may fire mail only into these

# A literal address; Pleasanter placeholders such as [Manager] and pls references ${env:x} are not matched.
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+\-${])[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")

# Sections of SiteSettings whose elements send mail (process notifications are nested in Processes).
SITE_SECTIONS = ("Notifications", "Reminders")


def effects(env_conf: dict) -> dict:
    """The declared side effects of one environment, with defaults. Raises ValueError on an unknown value."""
    se = env_conf.get("side_effects") or {}
    if not isinstance(se, dict):
        raise ValueError(f"side_effects = {se!r}; expected an object such as {{'mail': 'unknown', 'jobs': 'unknown'}}")
    mail, jobs = se.get("mail", "unknown"), se.get("jobs", "unknown")
    if mail not in MAIL_STATES:
        raise ValueError(f"side_effects.mail = {mail!r}; expected one of {', '.join(MAIL_STATES)}")
    if jobs not in JOB_STATES:
        raise ValueError(f"side_effects.jobs = {jobs!r}; expected one of {', '.join(JOB_STATES)}")
    return {"mail": mail, "jobs": jobs}


_MAIL_RISK = {"sink": 0, "disabled": 0, "live": 1, "unknown": 2}
_JOB_RISK = {"disabled": 0, "live": 1, "unknown": 2}


def cautious(own: dict, base: dict) -> dict:
    """Side effects of a sandbox (ADR-0011): it shares its base environment's server (SMTP) and tenant (scheduled
    scripts), so the riskier of its own copy and the base's current value counts; on a tie the base's value."""
    return {"mail": own["mail"] if _MAIL_RISK[own["mail"]] > _MAIL_RISK[base["mail"]] else base["mail"],
            "jobs": own["jobs"] if _JOB_RISK[own["jobs"]] > _JOB_RISK[base["jobs"]] else base["jobs"]}


def _keys(items: list | None) -> list[tuple[str, dict]]:
    """(key, item) for the dict items of a list. Key = Id (stable in Pleasanter), prefixed by the Name when there is
    one (processes), else the list position. Names are not unique in Pleasanter, so a clash gets '#<index>'."""
    out, seen = [], set()
    for i, it in enumerate(items or []):
        if not isinstance(it, dict):
            continue
        k = str(it["Id"]) if "Id" in it else f"#{i}"
        if it.get("Name"):
            k = f"{it['Name']}:{k}"
        if k in seen:
            k = f"{k}#{i}"
        seen.add(k)
        out.append((k, it))
    return out


def mail_elements(settings: dict) -> dict[str, Any]:
    """Every element of a site that can send mail, keyed by a stable path such as
    'Notifications[1]', 'Reminders[2]' or 'Processes[return:1].Notifications[1]'.
    Disabled elements and non-mail notification types are included on purpose: the guard errs on the safe side."""
    out: dict[str, Any] = {}
    for sec in SITE_SECTIONS:
        for k, it in _keys(settings.get(sec)):
            out[f"{sec}[{k}]"] = it
    for pk, p in _keys(settings.get("Processes")):
        for nk, n in _keys(p.get("Notifications")):
            out[f"Processes[{pk}].Notifications[{nk}]"] = n
    return out


def changed_mail_elements(before: dict, after: dict) -> list[str]:
    """Mail-sending elements added, removed or changed between two SiteSettings (live → git)."""
    a, b = mail_elements(before), mail_elements(after)
    canon = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)   # noqa: E731
    out = []
    for k in sorted(set(a) | set(b)):
        if k not in a:
            out.append(f"{k} added")
        elif k not in b:
            out.append(f"{k} removed")
        elif canon(a[k]) != canon(b[k]):
            out.append(f"{k} changed")
    return out


def literal_addresses(settings: dict) -> list[tuple[str, str]]:
    """(element path, address) for every literal mail address inside a mail-sending element (lint L-MAIL-01).
    Every string field is scanned, so reminder address fields are covered without relying on their names."""
    found = []

    def walk(path: str, v: Any) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                walk(path, x)
        elif isinstance(v, list):
            for x in v:
                walk(path, x)
        elif isinstance(v, str):
            for m in EMAIL_RE.findall(v):
                found.append((path, m))
    for path, el in mail_elements(settings).items():
        walk(path, el)
    return found


def test_writes(spec: dict) -> bool:
    """True when a test spec changes data or executes a process (which fires notifications)."""
    return any(st.get("op") in ("create", "update", "delete", "exec") for st in spec.get("steps") or [])


def test_sites(spec: dict, default_site: Any, all_sites: set) -> set[str]:
    """Site ids a spec writes to, as pls_http.run_tests sends the requests:
    - create -> its `site`, else the command's site (never `run_on`, which only selects the configuration read);
    - update / delete / exec on a record created earlier in the spec -> that create's site;
    - update / delete / exec on any other record (a --var fixture) -> its site is unknown, so every site of the env."""
    sites, created = set(), {}
    for st in spec.get("steps") or []:
        op = st.get("op")
        if op == "create":
            site = str(st.get("site") or default_site)
            sites.add(site)
            if st.get("save"):
                created[st["save"]] = site
        elif op in ("update", "delete", "exec"):
            var = str(st.get("record") or "").lstrip("$")
            if var in created:
                sites.add(created[var])
            else:
                sites |= {str(x) for x in all_sites} | {str(default_site)}
    return sites


def test_refusal(env: str, eff: dict, mailing_sites: dict[str, list[str]]) -> str | None:
    """Reason to refuse a test run, or None. mailing_sites: site id → its mail-sending elements (live)."""
    if eff["mail"] in MAIL_SAFE or not mailing_sites:
        return None
    detail = "; ".join(f"site {s}: {', '.join(els[:3])}{' …' if len(els) > 3 else ''}" for s, els in sorted(mailing_sites.items()))
    return (f"REFUSED (ADR-0010): these tests change records on sites that send mail ({detail}), and envs.{env}.side_effects.mail "
            f"is {eff['mail']!r}. Every notification and reminder counts, also disabled ones (safe side), and a record given by --var "
            "counts for every site of the env. A person checks the environment's SMTP and sets mail to 'sink' or 'disabled' first.")


def apply_refusal(env: str, eff: dict, changed: dict[str, list[str] | None]) -> tuple[str | None, str | None]:
    """(refusal, warning) for applying a release whose mail-sending elements changed. changed: site -> items, or None
    when the plan was made before this guard existed (its mail changes are unknown)."""
    unplanned = sorted(s for s, v in changed.items() if v is None)
    if unplanned and eff["mail"] not in MAIL_SAFE:
        return (f"REFUSED (ADR-0010): the plan does not record mail-sending changes for {', '.join(unplanned)} (planned before "
                f"this check) and envs.{env}.side_effects.mail is {eff['mail']!r}. Run pls release-plan again with a new release id."), None
    changed = {s: v for s, v in changed.items() if v}
    if not changed:
        return None, None
    detail = "; ".join(f"{s}: {', '.join(v)}" for s, v in sorted(changed.items()) if v)
    if eff["mail"] == "unknown":
        return (f"REFUSED (ADR-0010): the release changes mail-sending elements ({detail}) and envs.{env}.side_effects.mail is "
                "'unknown'. A person checks the environment's SMTP and records mail as sink, disabled or live."), None
    if eff["mail"] == "live":
        return None, f"WARNING (ADR-0010): {env} sends real mail; this release changes {detail}"
    return None, None


def describe(env: str, eff: dict) -> str:
    """One line for http-check."""
    tail = ("tests that change records on sites with notifications or reminders are refused"
            if eff["mail"] not in MAIL_SAFE else "tests may fire mail into the declared " + eff["mail"])
    jtail = {"unknown": "; writing tests and releases changing scheduled scripts are refused while the project declares any",
             "live": "; scheduled scripts run here (warning on writing tests)", "disabled": ""}[eff["jobs"]]
    return f"side effects: mail {eff['mail']}, jobs {eff['jobs']} — {tail}{jtail} (ADR-0010)"


# ---------------------------------------------------------------- scheduled server scripts (jobs, ADR-0012)

JOBS_DIR = Path("config") / "_tenant" / "scheduled-scripts"
JOBS_INDEX = "_index.json"


def _job_index(d: Path) -> dict[str, dict]:
    """name -> entry of _index.json (a list of objects with a unique, non-empty 'name'). Raises ValueError."""
    p = d / JOBS_INDEX
    if not p.exists():
        return {}
    try:
        idx = json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as ex:
        raise ValueError(f"{JOBS_INDEX} is not valid JSON ({ex})")
    if not isinstance(idx, list):
        raise ValueError(f"{JOBS_INDEX} must be a list of objects such as {{'name': 'nightly', 'schedule': '毎日 02:00', 'enabled': true}}")
    out: dict[str, dict] = {}
    for i, it in enumerate(idx):
        name = it.get("name") if isinstance(it, dict) else None
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{JOBS_INDEX}[{i}] has no 'name'")
        if not SAFE_NAME.fullmatch(name):                  # the name is also the body's file stem (Windows: case-blind)
            raise ValueError(f"{JOBS_INDEX}[{i}]: name {name!r} must be lowercase letters, digits, '-' or '_' "
                             "(it names <name>.js; keep the Japanese title in another field)")
        if name in out:
            raise ValueError(f"{JOBS_INDEX}: name {name!r} is used twice")
        out[name] = it
    return out


def _bodies(d: Path) -> dict[str, bytes]:
    return {p.stem: p.read_bytes() for p in d.glob("*.js") if p.is_file()}


def job_problems(r: Path) -> list[str]:
    """Layout problems of the declared jobs (lint L-JOB-01): bad index, entry without body, body without entry."""
    d = r / JOBS_DIR
    if not d.is_dir():
        return []
    try:
        idx = _job_index(d)
    except ValueError as ex:
        return [str(ex)]
    bodies = set(_bodies(d))
    return ([f"{n}.js: file name must be lowercase letters, digits, '-' or '_'" for n in sorted(bodies) if not SAFE_NAME.fullmatch(n)] +
            [f"{n}: listed in {JOBS_INDEX} but {n}.js is missing" for n in sorted(set(idx) - bodies)] +
            [f"{n}.js: not listed in {JOBS_INDEX} (schedule and enabled flag unknown)" for n in sorted(bodies - set(idx))])


def load_jobs(r: Path, render: Callable[[Any], Any] | None = None) -> dict[str, dict]:
    """Scheduled scripts the project declares: name -> {"entry": index entry or None, "body": text or None}, with
    ${site:x} / ${principal:x} / ${env:x} resolved by `render` for one environment (what the operator deploys there).
    An entry without a body, or a body without an entry, still counts (safe side). Raises ValueError on a bad index or a
    body that is not UTF-8. Bodies keep their line endings: config/** is stored without conversion (.gitattributes)."""
    d = r / JOBS_DIR
    if not d.is_dir():
        return {}
    render = render or (lambda x: x)
    idx = _job_index(d)
    out = {}
    for name, raw in sorted(_bodies(d).items()):
        try:
            out[name] = {"entry": None, "body": render(raw.decode("utf-8"))}
        except UnicodeDecodeError:
            raise ValueError(f"{name}.js is not UTF-8")
    for name, it in idx.items():
        out.setdefault(name, {"entry": None, "body": None})["entry"] = render(it)
    return dict(sorted(out.items()))


def fingerprints(jobs: dict[str, dict]) -> dict[str, str]:
    """name -> sha256 of the (rendered) index entry and body: a change of either, or of an environment value they use,
    is a change of the job on that environment."""
    out = {}
    for name, j in jobs.items():
        h = hashlib.sha256(json.dumps(j["entry"], ensure_ascii=False, sort_keys=True).encode("utf-8"))
        h.update(b"|body|" + (j["body"].encode("utf-8") if j["body"] is not None else b"|missing|"))
        out[name] = h.hexdigest()
    return out


def declared_jobs(r: Path) -> dict[str, str]:
    """Fingerprints of the scheduled scripts as written in git (unrendered); empty when the project declares none."""
    return fingerprints(load_jobs(r))


def valid_fingerprints(v: Any) -> bool:
    return isinstance(v, dict) and all(isinstance(k, str) and isinstance(x, str) for k, x in v.items())


def changed_jobs(before: dict[str, str] | None, after: dict[str, str]) -> list[str]:
    """Jobs added, removed or changed since the fingerprints of the last applied release (None: none recorded)."""
    if before is None:
        return [f"{n} added (no applied release of this environment records the scheduled scripts)" for n in sorted(after)]
    out = []
    for n in sorted(set(before) | set(after)):
        if n not in before:
            out.append(f"{n} added")
        elif n not in after:
            out.append(f"{n} removed")
        elif before[n] != after[n]:
            out.append(f"{n} changed")
    return out


def jobs_test_refusal(env: str, eff: dict, jobs: dict[str, str]) -> tuple[str | None, str | None]:
    """(refusal, warning) for tests that change records. A scheduled script runs tenant-wide on its own schedule and
    is not tied to one site, so every declared job counts for every writing test (safe side)."""
    if not jobs or eff["jobs"] == "disabled":
        return None, None
    names = ", ".join(sorted(jobs))
    if eff["jobs"] == "unknown":
        return (f"REFUSED (ADR-0010, ADR-0012): these tests change records, the project declares scheduled server scripts ({names}) "
                f"and envs.{env}.side_effects.jobs is 'unknown'. A scheduled script can act on the test records (update them, "
                "mail about them) on its next run. A person checks whether scheduled scripts run on this environment and records "
                "jobs as 'disabled' or 'live'."), None
    return None, f"WARNING (ADR-0010): scheduled scripts run on {env} ({names}); they may act on the records these tests create"


def jobs_apply_refusal(env: str, eff: dict, changed: list[str] | None, declared: bool) -> tuple[str | None, str | None]:
    """(refusal, warning) for applying a release. changed: the plan's job changes, or None when the plan was made before
    this check (its job changes are unknown); declared: the project declares jobs now."""
    if changed is None:
        if declared and eff["jobs"] != "disabled":
            return (f"REFUSED (ADR-0010): the plan does not record scheduled-script changes (planned before this check), the "
                    f"project declares scheduled scripts and envs.{env}.side_effects.jobs is {eff['jobs']!r}. "
                    "Run pls release-plan again with a new release id."), None
        return None, None
    if not changed:
        return None, None
    detail = "; ".join(changed)
    if eff["jobs"] == "unknown":
        return (f"REFUSED (ADR-0010): the release changes scheduled scripts ({detail}) and envs.{env}.side_effects.jobs is "
                "'unknown'. A person checks whether scheduled scripts run on this environment and records jobs as "
                "'disabled' or 'live'."), None
    if eff["jobs"] == "live":
        return None, f"WARNING (ADR-0010): scheduled scripts run on {env}; this release changes {detail}"
    return None, None


def manual_job_step(env: str, changed: list[str], release: str = "<release>") -> str | None:
    """The manual deploy and verification step of a release that changes scheduled scripts (ADR-0012 option B)."""
    if not changed:
        return None
    return (f"MANUAL (ADR-0012): scheduled scripts are not deployed by pls. After the sites of this release are applied "
            f"(never if the apply was rolled back), on {env}, tenant management → サーバスクリプト: "
            f"{'; '.join(changed)} — copy each body from releases/{release}/scheduled-scripts/<name>.js (references resolved "
            f"for {env}) with its schedule and enabled flag from {JOBS_INDEX} there. Then a person compares the tenant scripts "
            f"with those files and records it: pls jobs-verified {release} --by <name> --quote \"<their words>\". Until then the "
            "next release lists these changes again.")


def bad_plan_jobs(pj: Any) -> str | None:
    """Why a plan's `jobs` record cannot be trusted (hand-edited), or None. A missing record is handled by the caller."""
    if not isinstance(pj, dict):
        return "plan.jobs is not an object"
    ch = pj.get("changed")
    if not isinstance(ch, list) or not all(isinstance(x, str) for x in ch):
        return "plan.jobs.changed is not a list of strings"
    if pj.get("fingerprints") is not None and not valid_fingerprints(pj["fingerprints"]):
        return "plan.jobs.fingerprints is not an object of name → sha256"
    if pj.get("manual_step") is not None and not isinstance(pj["manual_step"], str):
        return "plan.jobs.manual_step is not text"
    return None
