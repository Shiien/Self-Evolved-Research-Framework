---
name: checklist
description: All checklist-tree write operations in one mode-based skill — CREATE (add a leaf or branch task with L2 sub-checklist / paper audit template), UPDATE (mark items done, add discovered work, annotate artifacts; also handles user progress reports, absorbing the former progress-capture), VERIFY (promote [x]→[v] by checking artifacts, running verification scripts, spot-checking numbers, validating paper cross-references), and RECOUNT (rewrite stale branch caches). Absorbs the former checklist-create / checklist-update / checklist-verify / checklist-status / progress-capture skills — those names now refer to modes here. Read-only status reporting moved to `python -m harness status`. Triggers on "add a task", "track this", "mark done", "I finished X", "I did X today", "update the checklist", "verify the checklist", "create a checklist for the paper".
---

# checklist

**Shared context**: Read `skills/_shared/checklist-engine.md` first (tree
structure L0→L1→L2, marker vocabulary `[ ]`→`[x]`→`[v]`→`[U]`, category
templates incl. the 8-part paper audit).

**Scope note**: read-only progress *reporting* is `python -m harness status`
(deterministic, always fresh-counts). This skill owns all *writes* to the
tree. Checklists track deliverables — experiment evidence lives in
`RESEARCH_STATE.md`, never here.

## Mode: CREATE — "add a task", "track X", "checklist for the paper"

1. Classify: term (`short-term` days–1wk / `mid-term` wks–1mo / `long-term`)
   and category (`idea` / `method` / `experiment` / `paper`).
2. **Leaf fast-path** (atomic task): append to `checklists/{term}.md` under
   `## {Category}`:
   `- [ ] {description} — \`{artifact_path}\`  <!-- added {YYYY-MM-DD} -->`
   then refresh the L0 count + timestamp. Done (2 file writes).
3. **Branch path** (needs decomposition): add
   `- [0/N] {description} → checklists/{term}/{category}-{slug}.md` to L1;
   create the L2 file from the matching template in `checklist-engine.md`
   (`category=paper` → full 8-part audit template); refresh L1 + L0 counts.
4. Output: `[CHECKLIST] Created: {leaf|branch} in {term}/{category} | Progress: {term} [{done}/{total}]`

## Mode: UPDATE — "I finished X", "I did X today", "mark done", chained from artifact-producing skills

Also absorbs the former `progress-capture` skill: when the user reports
progress, route the pieces to their owners — deliverable completions are
marked here; scientific findings/decisions go to `RESEARCH_STATE.md`
(evidence/hypotheses); resolved experiments update `EXPERIMENTS.json`;
durable non-scientific facts go to `memory` (write mode). No separate
progress log file.

1. Match affected item(s) by description, artifact path, or category.
2. `[ ]` → `[x]`; append artifact path (`— {path}`) and
   `<!-- completed {YYYY-MM-DD} -->`. **Edit only the item's own file** —
   branch counts are caches, recomputed by RECOUNT / session-close
   (deferred propagation keeps updates to 1-2 file writes).
3. Add `[ ]` items for newly discovered work; decomposition-worthy tasks →
   CREATE mode.
4. Output: `[CHECKLIST] Updated: +{added}, {completed} marked [x] (counts deferred)`

## Mode: VERIFY — "verify the checklist", pre-submission, milestones

1. Walk the tree (L0 → L1 → L2); collect all `[x]` items.
2. Per item: artifact path exists? linked verification script passes?
   claimed numbers reproduce from the data file (within tolerance)? paper
   items: `\ref{}` targets and `\includegraphics` paths resolve, figure →
   script → data provenance intact?
3. All checks pass → promote to `[v]`. Any failure → stays `[x]` with a flag
   comment (`<!-- MISSING: ... -->` / `<!-- DISCREPANCY: claimed {X},
   computed {Y} -->`). Never downgrade `[v]`/`[U]`.
4. Chain into RECOUNT, then output the verification table.

## Mode: RECOUNT — stale caches, session-close

Recompute every branch `[M/N]` from its children (done = `[x]`+`[v]`+`[U]`),
propagate L2 → L1 → L0, refresh `Updated:` timestamps, write back changed
files only.

**Inputs**: user report / skill artifact / tree files
**Outputs**: updated tree files (+ inline summary)
**Token**: ~1-3K (leaf/update) · ~3-5K (branch create / full verify)
**Composition**: VERIFY before milestones; UPDATE chained from any skill that
produces an artifact; significant creations → `memory` (write mode) only if a
durable non-scientific fact was learned.
