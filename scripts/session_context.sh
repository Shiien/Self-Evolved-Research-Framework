#!/usr/bin/env bash
# SessionStart hook: deterministic session context for session-open.
# Replaces the v5 "silently read 5 files" protocol — the model formats this
# instead of re-reading state files. Fail-open: never blocks a session.
set -u
cd "$(dirname "$0")/.." 2>/dev/null || exit 0

echo "=== SER session context (scripts/session_context.sh) ==="

# Current research question (first non-empty line of the section)
if [ -f RESEARCH_STATE.md ]; then
  q=$(awk '/^## Current research question/{f=1;next} /^## /{f=0} f && NF {printf "%s ", $0}' RESEARCH_STATE.md | cut -c1-300)
  echo "[question] ${q:-'(none set — RESEARCH_STATE.md has no question)'}"
else
  echo "[question] RESEARCH_STATE.md missing — create it before research work"
fi

# Experiment ledger counts + next planned
if [ -f EXPERIMENTS.json ]; then
  python3 - <<'PY' 2>/dev/null || echo "[ledger] EXPERIMENTS.json unreadable"
import json
d = json.load(open("EXPERIMENTS.json"))
exps = d.get("experiments", [])
counts = {}
for e in exps:
    counts[e["status"]] = counts.get(e["status"], 0) + 1
nxt = next((e for e in exps if e["status"] == "planned"), None)
print(f"[ledger] {counts or 'empty'}")
print(f"[next-planned] {nxt['id'] + ': ' + nxt['question'] if nxt else '(none — plan one)'}")
PY
else
  echo "[ledger] EXPERIMENTS.json missing"
fi

# Most recent run + verdict
if [ -d runs ]; then
  last=$(ls -1 runs 2>/dev/null | tail -1)
  if [ -n "${last:-}" ]; then
    python3 - "$last" <<'PY' 2>/dev/null || echo "[last-run] runs/$last (unreadable)"
import json, sys
rid = sys.argv[1]
try:
    state = json.load(open(f"runs/{rid}/status.json"))["state"]
except Exception:
    state = "?"
verdict = "-"
try:
    ev = json.load(open(f"runs/{rid}/eval/result.json"))
    verdict = f"{ev['verdict']} ({ev['evidence_strength']})"
except Exception:
    pass
print(f"[last-run] {rid} state={state} verdict={verdict}")
PY
  else
    echo "[last-run] (none yet)"
  fi
fi

# Git state
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
dirty=$(git status --porcelain 2>/dev/null | wc -l)
lastc=$(git log --oneline -1 2>/dev/null)
echo "[git] branch=${branch:-?} dirty_files=${dirty:-?} last='${lastc:-?}'"

# Memory index pointer (bodies loaded on demand via memory-retrieve)
[ -f memory/MEMORY.md ] && echo "[memory] memory/MEMORY.md present ($(grep -c '^- ' memory/MEMORY.md 2>/dev/null || echo 0) entries)"

echo "=== end SER session context ==="
exit 0
