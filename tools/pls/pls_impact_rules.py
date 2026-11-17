"""Impact rules for P2 designs: one source for what `pls classify` decides and what a design must state (ADR-0029 A2).

Each rule has a stable id. Rules with `cls` are decided by `pls.classify` (the id is in its result under "rules");
rules without `cls` are design conditions no tool decides — the designer walks them, and `pls check p2` will ask
for an impact row per triggered rule (ADR-0029 Part B). KB ids point to rows of
`skills/pls-kb-pleasanter/references/behaviours.md`; their "Do this" text is copied into the generated reference.
A design condition's own text must only restate what its KB rows or the `pls` code say (a pending KB observation is
not cited until it is committed); the conditions live here, not in the KB probe index, because several name `pls`
commands rather than Pleasanter behaviour.

The generated reference is `skills/pls-p2-solution-designer/references/impact-rules.md` (path below). It is
data: a change of a rule's text needs no skill eval; a change of the generator or of the hand-written walk
procedure (`impact-checklist.md`) does (Nam 2026-11-16, ADR-0029).

Regenerate:  python tools/pls/pls_impact_rules.py --write
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KB_BEHAVIOURS = ROOT / "skills/pls-kb-pleasanter/references/behaviours.md"
OUT = ROOT / "skills/pls-p2-solution-designer/references/impact-rules.md"

DATA, PERM, CFG = "data-impacting", "permission-impacting", "config-only"

# area, id, cls (None = design condition), trigger, what the design checks and states, KB ids, example
RULES: tuple[dict, ...] = (
    # ---- statuses
    dict(area="Statuses", id="ST-STATUS-CHANGE", cls=None,
         trigger="adds, removes or renames a **status**",
         design="views with `Status` filters; notifications watching `Status` or using a view as condition; "
                "aggregations by status; process `CurrentStatus` / `ChangedStatus`; status controls; scripts with "
                "status maps",
         kb=["D9"], example="an \"open items\" view filtering on the old statuses would hide records in the new "
                            "status → derived requirement; a script mapping status codes to labels needs the new code"),
    # ---- choices
    dict(area="Choices", id="CL-CHOICES-REMOVED", cls=DATA,
         trigger="removes a **choice** from a column's `ChoicesText`",
         design="records holding the removed value (migration or nothing to convert); filters and conditions listing it",
         kb=["D11"], example=""),
    dict(area="Choices", id="CL-CHOICES-ADDED", cls=CFG,
         trigger="adds or reorders **choices** (none removed)",
         design="filters, process conditions and notifications that list choices: do they need the new one?",
         kb=[], example=""),
    dict(area="Choices", id="CL-MULTISELECT-SWITCH", cls=DATA,
         trigger="switches `MultipleSelections` of a column on or off",
         design="existing values are read as a JSON array when it is on and as one value when it is off "
                "(source-derived, not verified): convert the stored values, or nothing to convert on an empty site",
         kb=[], example=""),
    dict(area="Choices", id="CL-MULTISELECT-EXPLICIT-FALSE", cls=CFG,
         trigger="adds or removes an explicit `MultipleSelections: false`",
         design="nothing (Pleasanter records only true)", kb=["D8"], example=""),
    dict(area="Choices", id="CL-CHOICE-CONTROL", cls=DATA,
         trigger="changes `ChoicesControlType` (drop-down / radio)",
         design="on a multi-select column radio buttons show stored values as empty and a save may overwrite them "
                "(source-derived, not verified): check the column's stored values",
         kb=[], example=""),
    # ---- columns
    dict(area="Columns", id="CO-COLUMN-ADD", cls=None,
         trigger="adds a **column**",
         design="an existing column already holding the same data (raise to P1/G1 instead of adding); slot free and "
                "never used with data (slot ledger, ADR-0002); editor layout; grid; filters; exports; scripts that "
                "iterate columns (`pls xref`)",
         kb=[], example="a stamp column set by a process is read-only and placed next to related fields"),
    dict(area="Columns", id="CL-COLUMN-REMOVED", cls=DATA,
         trigger="removes a **column** definition",
         design="data in the slot → migration; formulas, links, lookups and scripts referencing it",
         kb=[], example=""),
    dict(area="Columns", id="CL-DEFAULT-INPUT", cls=DATA,
         trigger="changes a column's `DefaultInput`",
         design="which records the new default reaches (existing values are not known to change: no KB row, not "
                "verified) — state what the requirement wants",
         kb=[], example=""),
    # ---- links, lookups, summaries
    dict(area="Links, lookups, summaries", id="LK-SITE-REFERENCES", cls=None,
         trigger="adds or changes a **cross-site reference** (link, lookup, summary, script site id)",
         design="every site id is written `${site:<name>}` and resolves in every environment",
         kb=["D3"], example=""),
    dict(area="Links, lookups, summaries", id="CL-LOOKUP-CHANGED", cls=DATA,
         trigger="changes a link / lookup definition (JSON form of `ChoicesText`)",
         design="whether values already copied into existing records change is not known (no KB row, not "
                "verified) — state what the requirement wants; the conditions of LK-LOOKUP-SCREEN apply to the new "
                "definition",
         kb=["D40"], example=""),
    dict(area="Links, lookups, summaries", id="CL-LOOKUP-UNCHANGED", cls=CFG,
         trigger="re-orders or re-formats a link / lookup definition without changing it",
         design="nothing", kb=[], example=""),
    dict(area="Links, lookups, summaries", id="LK-LOOKUP-SCREEN", cls=None,
         trigger="uses a **link lookup** (a value copied from the master when a person chooses it)",
         design="自動ポストバック on the link column; a branch that does not depend on the lookup (the person or the "
                "client can still write the value) until a screen check passes on the site deployed by `updatesite` "
                "(link lists master records, value filled and stored after save / reopen, per creating role); an API "
                "create in the probed shape got no value (cause open) → API clients and imports write the value (D40; "
                "migrations: not covered by the KB — treat them the same); `release-plan` does not refuse these "
                "settings (inside `Columns`), so the design states the check",
         kb=["D40"], example="a 単価 looked up from the item master: the line's 単価 stays editable until the dev "
                             "screen check after the release passes"),
    dict(area="Links, lookups, summaries", id="LK-FORMULA-OVER-LOOKUP", cls=None,
         trigger="computes a formula over a **looked-up** value",
         design="not relied on over a looked-up operand on 1.5.2: an open question in the design plus a branch where "
                "the client writes both operands",
         kb=["D41", "D41a"], example=""),
    dict(area="Links, lookups, summaries", id="CL-SUMMARIES", cls=DATA,
         trigger="adds or changes a **summary** (サマリ tab — not 集計, which is the grid aggregation)",
         design="existing destination values are not recalculated: after the release an administrator presses 同期 on "
                "the サマリ tab per summary per environment (observed to recalculate on 1.5.2), a check of one parent, "
                "`pls step` (ADR-0028); updating one child per parent is the observed fallback and rewrites "
                "更新日時 / 更新者 (tell the customer)",
         kb=["D16"], example=""),
    # ---- formulas
    dict(area="Formulas", id="CL-FORMULAS", cls=DATA,
         trigger="adds, removes, reorders, enables or edits a **formula** (`Formulas[]`)",
         design="stored values of existing records are not known to be recomputed: the recomputed values as data, or "
                "同期 / SynchronizeFormulas on the screen (source-derived, not verified); nothing to convert only on an "
                "empty site and never for production",
         kb=["D41"], example=""),
    # ---- processes
    dict(area="Processes", id="PR-PROCESS-ADD", cls=None,
         trigger="adds a **process / button**",
         design="who may execute it (access control, CL-PROCESS-ACCESS); repeat execution; a display condition "
                "(D21: a process without a View fails); behaviour outside the condition (the API enforces it, D10)",
         kb=["D10", "D21"], example="who may press it is an open question unless the requirement says so; repeat "
                                    "execution prevented by the display condition on status"),
    dict(area="Processes", id="CL-PROCESS-ACCESS", cls=PERM,
         trigger="changes who may execute a process (`Processes[].Groups / Users / Depts`)",
         design="for each role, which buttons it sees and may press; a test with a user of that role (P4)",
         kb=["D20"], example=""),
    # ---- status controls, permissions, access lists
    dict(area="Permissions", id="CL-STATUS-CONTROL", cls=PERM,
         trigger="adds or changes a **status control** (`StatusControls[]`)",
         design="who may change a record in that status; a per-column ReadOnly does not stop an API update; the "
                "screen effect is checked by a person with a non-administrator user",
         kb=["D42"], example=""),
    dict(area="Permissions", id="CL-PERMISSIONS", cls=PERM,
         trigger="changes **site permissions** or a permission setting",
         design="permission matrix before / after; inherited child sites; for each restricted role, which process "
                "buttons still show (D19) → process access control (D20); principals per environment (`${principal:x}`)",
         kb=["D19", "D20"], example="a read-only 監査 role still sees the 督促 button and gets 403 when pressing it → "
                                    "restrict the process to the roles that may use it"),
    dict(area="Permissions", id="CL-ACCESS-LIST", cls=PERM,
         trigger="changes the access list of a view, export or dashboard part",
         design="who sees the view / export / part in each environment; principals as `${principal:x}`",
         kb=["D20"], example=""),
    dict(area="Permissions", id="RO-ROLES", cls=None,
         trigger="names a **role** (`design/roles.json`)",
         design="each role binds to a group, a user or a department (`\"principal\": \"Dept\"`, bound by `dept_code` "
                "or `dept_name`, never created by `pls principals`)",
         kb=[], example=""),
    # ---- notifications
    dict(area="Notifications", id="NO-NOTIFICATION-CHANGE", cls=None,
         trigger="adds or changes **notifications or reminders**",
         design="recipients exist in every environment (`${principal:x}`, no literal addresses: L-MAIL-01); mail is "
                "usually not testable on dev → an open point; no token, webhook URL or credential header in the "
                "configuration (L-SEC-01 refuses them, ADR-0005); the site's default mail addresses (`MailToDefault`, "
                "…) are set on the screen of each environment, never in git (ADR-0010)",
         kb=["D47"], example=""),
    # ---- scripts
    dict(area="Scripts", id="SC-SCRIPT-CHANGE", cls=None,
         trigger="adds or changes a **script**",
         design="ladder reason (I5); no hard-coded site ids (D3); no secrets (D5); no top-level const / let in a "
                "shared script (D7); timeouts",
         kb=["D3", "D5", "D7"], example=""),
    # ---- anything else
    dict(area="Other settings", id="SE-SCOPE", cls=None,
         trigger="changes the settings of a site (any key)",
         design="`pls scope --site <s>` lists every component of the site without round-trip evidence: each one the "
                "design adds or keeps needs a probe before G2 or a decision record (release-plan refuses them "
                "otherwise, ADR-0001)",
         kb=[], example=""),
    dict(area="Other settings", id="CL-OTHER", cls=CFG,
         trigger="any other setting",
         design="nothing beyond the walk above", kb=[], example=""),
)

BY_ID = {r["id"]: r for r in RULES}


def kb_advice(path: Path = KB_BEHAVIOURS) -> dict[str, str]:
    """KB id → its "Do this" text (last column of behaviours.md)."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (D\d+[a-z]?) \|", line)
        if m:
            out[m.group(1)] = line.rstrip().rstrip("|").rsplit(" | ", 1)[-1].strip()
    return out


def render(advice: dict[str, str] | None = None) -> str:
    advice = kb_advice() if advice is None else advice
    lines = ["# Impact rules (generated — do not edit)", "",
             "Generated by `python tools/pls/pls_impact_rules.py --write` from `tools/pls/pls_impact_rules.py` and "
             "the KB (`skills/pls-kb-pleasanter/references/behaviours.md`). How to walk them: `impact-checklist.md`.",
             "", "**Class:** set by `pls classify` for the built change (`data-impacting`, `permission-impacting`, "
             "`config-only`); *design* = a condition no tool decides — the design states it.", ""]
    area = None
    cited: list[str] = []
    for r in RULES:
        if r["area"] != area:
            area = r["area"]
            lines += [f"## {area}", "", "| Rule | If the change… | Class | The design checks and states | KB | Example |",
                      "|---|---|---|---|---|---|"]
        kb = ", ".join(r["kb"])
        cited += [k for k in r["kb"] if k not in cited]
        lines.append(f"| {r['id']} | {r['trigger']} | {r['cls'] or '*design*'} | {r['design']} | {kb} | "
                     f"{r['example'] or '—'} |")
        nxt = RULES.index(r) + 1
        if nxt == len(RULES) or RULES[nxt]["area"] != area:
            lines.append("")
    lines += ["## KB advice cited above (\"Do this\", verbatim)", ""]
    for k in sorted(cited, key=lambda x: (int(re.sub(r"\D", "", x)), x)):
        lines.append(f"- **{k}:** {advice.get(k, '(missing in the KB)')}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = render()
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")      # the Windows console code page cannot print it
    if sys.argv[1:] == ["--write"]:
        OUT.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
    else:
        sys.stdout.write(text)
