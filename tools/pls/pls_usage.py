"""LLM token usage per step (ADR-0013), read from Claude Code transcripts — numbers only, never conversation text.

Claude Code writes every model response to `<config>/projects/<encoded project path>/<session>.jsonl` (subagents in
`<session>/subagents/agent-*.jsonl`, with `agent-*.meta.json` holding the agent's description). Each response carries
`requestId`, `timestamp`, `message.model` and `message.usage` (input, cache creation, cache read, output tokens); one
response may be split into several lines with the same `requestId`, so usage is counted once per request.

A request is attributed to the step that was open at its timestamp (step markers in the run log, `pls step`).
`pls usage collect` writes one file per transcript session, `ops/usage/<session>.json`, overwritten on every collect
(idempotent; one file per session, so parallel developers never edit the same file).
"""
from __future__ import annotations

import json
import os
import re
from bisect import bisect_right
from datetime import datetime, timedelta
from pathlib import Path

FIELDS = ("input", "cache_creation", "cache_read", "output")


def transcripts_dir(project: Path) -> Path:
    """Where Claude Code keeps the transcripts of sessions started in `project` (every non-alphanumeric → '-')."""
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(project.resolve()))


STEP_TIMEOUT = timedelta(hours=24)       # a step not followed by another one counts as closed after a day


def _ts(s: str | None) -> datetime | None:
    """Aware datetime; a timestamp without offset is taken as local time (never mixed naive/aware)."""
    if not s:
        return None
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()


def _requests(path: Path, agent: str) -> dict[str, dict]:
    """requestId → {ts, model, agent, input, cache_creation, cache_read, output} for one transcript file."""
    out: dict[str, dict] = {}
    with open(path, encoding="utf-8", errors="replace") as h:      # a damaged line must not stop the count
        for line in h:
            if '"usage"' not in line:
                continue
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get("message") or {}
            u = msg.get("usage")
            if o.get("type") != "assistant" or not u or msg.get("model") == "<synthetic>":
                continue                            # <synthetic>: messages Claude Code writes itself, no model call
            rid = o.get("requestId") or msg.get("id") or o.get("uuid")   # message id: the same on split lines
            row = {"ts": o.get("timestamp"), "model": msg.get("model"), "agent": agent,
                   "input": u.get("input_tokens") or 0, "cache_creation": u.get("cache_creation_input_tokens") or 0,
                   "cache_read": u.get("cache_read_input_tokens") or 0, "output": u.get("output_tokens") or 0}
            prev = out.get(rid)
            if prev is None:
                out[rid] = row
            else:                                   # the same response split over lines: keep the largest counts
                for f in FIELDS:
                    prev[f] = max(prev[f], row[f])
    return out


def sessions(tdir: Path) -> dict[str, list[tuple[Path, str]]]:
    """session id → [(transcript file, agent label)] — the main conversation and its subagents."""
    out: dict[str, list[tuple[Path, str]]] = {}
    for main in sorted(tdir.glob("*.jsonl")):
        sid = main.stem
        files = [(main, "main")]
        sub = tdir / sid / "subagents"
        for f in sorted(sub.glob("agent-*.jsonl")) if sub.exists() else []:
            meta = f.with_name(f.stem + ".meta.json")
            label = f.stem
            try:                                    # agent type + id only: the description is conversation text
                m = json.loads(meta.read_text(encoding="utf-8"))
                label = f"{m.get('agentType') or 'agent'} {f.stem.removeprefix('agent-')[:8]}"
            except (OSError, ValueError):
                pass
            files.append((f, label))
        out[sid] = files
    return out


def attribute(requests: list[dict], steps: list[dict]) -> list[dict]:
    """Sum requests per (step, agent, model). Steps: run-log events of kind 'step', any order."""
    marks = sorted(((t, s) for s in steps if (t := _ts(s.get("ts")))), key=lambda x: x[0])
    times = [t for t, _ in marks]
    agg: dict[tuple, dict] = {}
    for r in requests:
        t = _ts(r["ts"])
        i = bisect_right(times, t) - 1 if t else -1
        st = marks[i][1] if i >= 0 and t - times[i] <= STEP_TIMEOUT else None
        key = (st.get("run_id") if st else None, r["agent"], r["model"])
        a = agg.setdefault(key, {"step": key[0], "phase": st.get("phase") if st else None,
                                 "title": st.get("title") if st else "(no open step)",
                                 "agent": r["agent"], "model": r["model"], "requests": 0,
                                 "first": r["ts"], "last": r["ts"], **{f: 0 for f in FIELDS}})
        a["requests"] += 1
        for f in FIELDS:
            a[f] += r[f]
        a["first"], a["last"] = min(a["first"], r["ts"]), max(a["last"], r["ts"])
    return sorted(agg.values(), key=lambda a: a["first"] or "")


def collect(project: Path, steps: list[dict], tdir: Path | None = None, since: str | None = None) -> list[Path]:
    """Write ops/usage/<session>.json for every transcript session. `since` (ISO date) selects the sessions with a
    request on or after it; a selected session is always counted whole, so the file never loses earlier requests."""
    tdir = tdir or transcripts_dir(project)
    written = []
    for sid, files in sessions(tdir).items():
        reqs = []
        for f, label in files:
            reqs += list(_requests(f, label).values())
        if not reqs or (since and not any((r["ts"] or "") >= since for r in reqs)):
            continue
        rows = attribute(reqs, steps)
        out = project / "ops" / "usage" / f"{sid}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"v": 1, "session": sid, "collected": datetime.now().astimezone().isoformat(timespec="seconds"),
                                   "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        written.append(out)
    return written


def load(project: Path) -> list[dict]:
    rows = []
    for f in sorted((project / "ops" / "usage").glob("*.json")) if (project / "ops" / "usage").exists() else []:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        rows += [dict(r, session=doc.get("session")) for r in doc.get("rows") or []]
    return rows


def report(rows: list[dict], by: str = "phase") -> list[dict]:
    """Totals grouped by 'phase', 'step', 'agent' or 'model' (rows from load())."""
    keyf = {"phase": lambda r: r.get("phase") or "-", "step": lambda r: f"{r.get('phase') or '-'} {r.get('title')}",
            "agent": lambda r: r.get("agent") or "-", "model": lambda r: r.get("model") or "-"}[by]
    agg: dict[str, dict] = {}
    for r in rows:
        a = agg.setdefault(keyf(r), {"key": keyf(r), "requests": 0, **{f: 0 for f in FIELDS}})
        a["requests"] += r.get("requests") or 0
        for f in FIELDS:
            a[f] += r.get(f) or 0
    out = sorted(agg.values(), key=lambda a: -(a["input"] + a["cache_creation"] + a["cache_read"] + a["output"]))
    for a in out:
        a["total"] = a["input"] + a["cache_creation"] + a["cache_read"] + a["output"]
    return out
