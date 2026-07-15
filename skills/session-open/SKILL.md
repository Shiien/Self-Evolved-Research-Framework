---
name: session-open
description: Runs silently at the start of every conversation. Formats the deterministic context injected by the SessionStart hook (scripts/session_context.sh) — research question, experiment ledger, last run verdict, git state — into a one-screen SER status banner, then proceeds directly to the user's request. Fires before any other processing — triggered by conversation start, not by user words.
---

# session-open

**Trigger**: Every conversation start (automatic, before any other processing).

**Process**:
1. The `SessionStart` hook has already injected deterministic context between
   `=== SER session context ===` markers: `[question]`, `[ledger]`,
   `[next-planned]`, `[last-run]`, `[git]`, `[memory]`. **Do not re-read the
   files it covers** (`RESEARCH_STATE.md`, `EXPERIMENTS.json`, `runs/`).
2. Read `memory/MEMORY.md` pointers only if the user's request plausibly
   touches remembered context (`memory` retrieve mode on demand, not by default).
3. Output the status banner:
   ```
   [SER] {project} | Q: {current research question, ≤1 line}
   Ledger: {counts} | last run: {id} → {verdict or state}
   Next: {next planned experiment id+question, or "plan one"}
   ```
4. Append warnings only when true:
   - `[!] baseline unverified` if the last run failed or `[git]` shows a dirty
     tree with harness/test changes
   - `[!] no research question set` if RESEARCH_STATE.md is missing/empty
5. Proceed immediately to the user's request — no questions asked.

**Fallback** (hook context absent — e.g. hooks disabled): run
`bash scripts/session_context.sh` once and format its output as above.

**Inputs**: hook-injected context (free)
**Outputs**: status banner (inline, not saved)
**Token**: ~0.3K
**Composition**: none (always first)
