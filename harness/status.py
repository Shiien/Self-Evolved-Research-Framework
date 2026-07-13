"""`python -m harness status` — deterministic project status aggregation.

Absorbs the read/report paths of the retired `status-report` and
`checklist-status` skills: experiment ledger, recent runs, external GPU run
records, and checklist completion counts. Read-only — checklist cache
rewrites stay with the `checklist` skill.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# leaf markers: [ ] todo, [x] done, [v] verified, [U] user-signed-off
_LEAF_RE = re.compile(r"^\s*- \[( |x|v|U)\]", re.MULTILINE)
_BRANCH_RE = re.compile(r"^\s*- \[(\d+)/(\d+)\]", re.MULTILINE)


def ledger_summary(ledger_path: Path) -> Optional[dict]:
    if not ledger_path.exists():
        return None
    exps = json.loads(ledger_path.read_text(encoding="utf-8")).get("experiments", [])
    counts: Dict[str, int] = {}
    for e in exps:
        counts[e["status"]] = counts.get(e["status"], 0) + 1
    return {
        "counts": counts,
        "planned": [e for e in exps if e["status"] == "planned"],
        "running": [e for e in exps if e["status"] == "running"],
        "failed": [e for e in exps if e["status"] == "failed"],
    }


def runs_summary(runs_root: Path, limit: int = 5) -> List[dict]:
    if not runs_root.is_dir():
        return []
    out = []
    for d in sorted(runs_root.iterdir())[-limit:]:
        status_file = d / "status.json"
        if not status_file.exists():
            continue
        state = json.loads(status_file.read_text(encoding="utf-8"))["state"]
        verdict = "-"
        ev_file = d / "eval" / "result.json"
        if ev_file.exists():
            ev = json.loads(ev_file.read_text(encoding="utf-8"))
            verdict = f"{ev['verdict']} ({ev['evidence_strength']})"
        out.append({"id": d.name, "state": state, "verdict": verdict})
    return out


def external_summary(experiments_log_dir: Path) -> List[dict]:
    """Summarize logs/experiments/*.yaml (external GPU runs). Read-only —
    liveness polling stays with `experiment-monitor` for now (tranche 2)."""
    if not experiments_log_dir.is_dir():
        return []
    out = []
    for f in sorted(experiments_log_dir.glob("*.yaml")):
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            out.append({"exp_id": f.stem, "status": "unreadable", "machine": "?",
                        "has_contract": False})
            continue
        out.append({
            "exp_id": d.get("exp_id", f.stem),
            "status": d.get("status", "?"),
            "machine": d.get("machine", "?"),
            "has_contract": bool(d.get("contract")),
        })
    return out


def checklist_summary(repo_root: Path) -> Dict[str, dict]:
    """Fresh, read-only recount of leaf markers per L1 term file (+ its L2
    files). Branch `[M/N]` cache lines are ignored — children are counted
    directly, so stale caches cannot skew the report."""
    terms = {}
    for term in ("short-term", "mid-term", "long-term"):
        files = []
        l1 = repo_root / "checklists" / f"{term}.md"
        if l1.exists():
            files.append(l1)
        l2_dir = repo_root / "checklists" / term
        if l2_dir.is_dir():
            files.extend(sorted(l2_dir.glob("*.md")))
        counts = {" ": 0, "x": 0, "v": 0, "U": 0}
        for f in files:
            for m in _LEAF_RE.finditer(f.read_text(encoding="utf-8")):
                counts[m.group(1)] += 1
        total = sum(counts.values())
        done = counts["x"] + counts["v"] + counts["U"]
        terms[term] = {"done": done, "total": total, "blocked_signoff": counts["U"],
                       "verified": counts["v"], "todo": counts[" "]}
    return terms


def print_status(repo_root: Path, runs_root: Path) -> None:
    print("[STATUS] project status (deterministic; harness status)")

    led = ledger_summary(repo_root / "EXPERIMENTS.json")
    if led is None:
        print("  ledger: EXPERIMENTS.json missing")
    else:
        print(f"  ledger: {led['counts'] or 'empty'}")
        for e in led["failed"]:
            print(f"    [!] failed: {e['id']} — diagnose/resume before new runs")
        nxt = led["planned"][:2]
        for e in nxt:
            print(f"    next planned: {e['id']}: {e['question'][:90]}")

    runs = runs_summary(runs_root)
    print(f"  runs ({len(runs)} most recent):" if runs else "  runs: (none)")
    for r in runs:
        print(f"    {r['id']}  state={r['state']}  verdict={r['verdict']}")

    ext = external_summary(repo_root / "logs" / "experiments")
    if ext:
        print(f"  external runs ({len(ext)}):")
        for e in ext:
            flag = "" if e["has_contract"] else "  [!] NO CONTRACT"
            print(f"    {e['exp_id']}  {e['status']}  on {e['machine']}{flag}")

    terms = checklist_summary(repo_root)
    if any(t["total"] for t in terms.values()):
        parts = [f"{k} {v['done']}/{v['total']}" for k, v in terms.items() if v["total"]]
        print(f"  checklists: {' | '.join(parts)}")
        blocked = sum(t["blocked_signoff"] for t in terms.values())
        if blocked:
            print(f"    [U]-stage items awaiting user sign-off: {blocked}")

    state = repo_root / "RESEARCH_STATE.md"
    if state.exists():
        text = state.read_text(encoding="utf-8")
        n_ev = 0
        if "## Established evidence" in text:
            sec = text.split("## Established evidence", 1)[1].split("\n## ", 1)[0]
            n_ev = sum(1 for ln in sec.splitlines() if ln.lstrip().startswith("- "))
        print(f"  research state: evidence entries = {n_ev}")
    else:
        print("  [!] RESEARCH_STATE.md missing")
