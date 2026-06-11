---
name: code-review
description: Dual-reviewer code review. Review A (Claude) checks roadmap compliance — Done Criteria, per-step Acceptance, Constraints, Unplanned changes. Review B (Codex via `/codex:review`) checks code quality — logic, edge cases, security, API misuse, maintainability. The two reviews are merged into a classification table and a single PASS/FAIL verdict. Small tasks skip Review A and use lightweight mode (Review B + Claude quick check). Produces `docs/code_reviews/{name}.md`.
---

# code-review (Track B — Claude + Codex dual reviewer)

**Trigger**: Code changes are ready for review after `code-implement` completes, before commit.

**Shared context**: Before invoking Codex, Read `skills/_shared/codex-contract.md § 1, 5` for dependencies and error handling. Codex invocation here does not use the four-tag contract (that's only for `/codex:rescue`); `/codex:review` has its own interface.

**Track**: B. Installed via `--codex-track codex`. Requires `/codex:review` available at install time.

---

## Step 1 — Determine review mode

| Source of changes | Review mode |
|-------------------|-------------|
| Small task (Claude direct TDD, no roadmap) | **Lightweight** — skip Review A, run Review B + Claude quick check (Step 4) |
| Medium/Large task with roadmap | **Full** — both Review A and Review B, then merge (Steps 2 → 3 → 5) |

---

## Step 2 — Review A: Claude plan compliance

Identical to Track A `code-review` full mode (see `SKILL.claude.md § Step 3`).

### Inputs
- Roadmap `docs/implement_roadmap/YYYY-MM-DD-{name}.md`.
- `git diff {base_commit_sha}` (SHA from roadmap Status).
- `git status -s` for new/untracked files.
- Test results from running the Test command and each Done Criterion.

### Process
1. Run Done Criteria — record PASS / FAIL with evidence.
2. Per-step verification against Files + What to do + Acceptance.
3. Constraint compliance.
4. Goal check.

### Output A (appended into the merged report in Step 5)

```markdown
## Review A — Plan Compliance (Claude)

**Test suite**: {PASS / FAIL}

### Done Criteria
- [x] ... — PASS
- [ ] ... — FAIL: {why}

### Per-Step Verification
| Step | Title | Acceptance | Status | Notes |
|------|-------|------------|--------|-------|
...

### Constraint Violations
- ...

### Unplanned Changes
- ...

### Claude Assessment
{PASS / FAIL with one-line reason}
```

---

## Step 3 — Review B: Codex code quality

From Claude's main session, the `/codex:review` slash command is NOT reachable via the `Skill` tool (that path silently renders the command body as text without executing the underlying Bash — see `skills/_shared/codex-contract.md § 4` for the same pattern on rescue). There is also no dedicated `codex:codex-review` subagent. Invoke the same runner directly via `Bash`:

```bash
CODEX_PLUGIN_ROOT=$(ls -d ~/.claude/plugins/marketplaces/*/plugins/codex 2>/dev/null | head -1)
node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" review
```

For long reviews, set `run_in_background: true` on the `Bash` call and tell the user Codex review is running in the background. The stdout IS Codex's review output — preserve it verbatim in the merged report.

After the call returns, sanity-check with `ls -lt /tmp/codex-companion/*/jobs/ | head` that a new review job was created. If not, the path resolution failed — inspect `CODEX_PLUGIN_ROOT` and re-run.

Codex reviews the working tree diff independently. Its focus:
- Logic errors and edge cases
- Security issues (injection, auth, data exposure)
- API misuse or incorrect library usage
- Code clarity and maintainability
- Error handling gaps
- Performance concerns

### Codex output handling

- **Preserve Codex output verbatim.** Do not summarize or reinterpret.
- Expected structure: findings ordered by severity (critical → important → minor), each with file path, line number if applicable, description, and evidence. Overall assessment. Residual risks.
- If Codex output format differs, extract findings as-is — Step 5 normalizes them.

### If Codex is unavailable at runtime

If `/codex:review` fails (auth expired, service down), degrade to Track A behavior:
- Skip Review B.
- Emit the Review A verdict as the sole assessment.
- Note in the output: `Review B skipped — Codex unavailable ({cause}). Install/run \`/codex:setup\` to restore.`
- Continue to Step 5 with only Review A findings.

---

## Step 4 — Lightweight mode (small tasks)

For small tasks that did not go through the roadmap/implement flow:

1. **Skip Review A** (no roadmap to check against).
2. **Run Review B** via `/codex:review` for code quality.
3. **Claude quick check**: read the diff, confirm tests pass, confirm the change does what the user asked.
4. Emit a merged short report (Step 5 format, but "Review A" row replaced with "Claude quick check").

---

## Step 5 — Merge findings

Lay both reviews side by side and classify each finding:

| Pattern | Interpretation | Action |
|---------|---------------|--------|
| Both Review A and Review B flag the same issue | High-confidence real problem | **Must fix** |
| Only Review A: Acceptance criterion not met | Plan compliance gap | **Must fix** |
| Only Review A: Unplanned changes | Scope concern | Assess justification. If justified → note and pass. If not → **Must fix**. |
| Only Review B: logic / security / edge case | Code quality issue | **Must fix** if critical/important; **Note** if minor. |
| Contradictory findings | Disagreement | Examine evidence from both sides. Decide by grounding. |
| Neither flags issues | Clean | **Pass** |

### Decision rule

- **PASS** — all Done Criteria pass, no critical/important findings remain unfixed, both reviewers agree (or remaining disagreements are minor and assessed).
- **FAIL** — one or more critical/important findings remain.

---

## Step 6 — Produce the merged report

Save to `docs/code_reviews/YYYY-MM-DD-{roadmap-name}.md` (full mode) or `docs/code_reviews/quick-YYYY-MM-DD-{short-name}.md` (lightweight mode):

```markdown
# Code Review — {Roadmap Name}

**Roadmap**: `docs/implement_roadmap/{path}` (or `n/a` for lightweight)
**Base commit**: {SHA} (or `n/a` for lightweight)
**Test suite**: {PASS / FAIL}
**Reviewers**: Claude (Review A) + Codex (Review B)  -- or "Codex only" if A skipped, or "Claude only" if B unavailable.

## Review A — Plan Compliance (Claude)

{Output A from Step 2, verbatim}

## Review B — Code Quality (Codex)

{Codex output verbatim from Step 3}

## Merged Findings

| Finding | Source | Severity | Category | Action |
|---------|--------|----------|----------|--------|
| {one-line description} | both / A / B | critical / important / minor | plan / quality / security / ... | must fix / note / pass |
...

## Verdict

{PASS — ready for commit / FAIL — issues listed above need fixing}
```

---

## Step 7 — Deliver the verdict

- **PASS** → suggest `code-commit`.
- **FAIL** → surface report to user. Do NOT auto-loop back to `code-implement`. User decides: manual fix, re-run `code-implement`, redesign roadmap, or commit with known issues.

---

## Architectural Note

Track B separates review into two non-overlapping roles:
- **Review A (Claude, main session)** — plan compliance. Does the implementation achieve the research goal the roadmap stated?
- **Review B (Codex, `/codex:review`)** — code quality. Logic, edges, security, maintainability.

Different models, different biases, different questions. A single session cannot self-review effectively; this is why dual review exists.

When Codex is unavailable the skill degrades to Review A only (Track A behavior) and the user is notified so they can re-run later or run external review.

---

## Output

```
[code-review / codex] Review complete — {PASS | FAIL}
  Mode: {full | lightweight | degraded (B unavailable)}
  Report: docs/code_reviews/{path}
  Next: code-commit (if PASS) or user decision (if FAIL)
```

**Inputs**: `git diff {base_sha}` + `git status` + roadmap (if any) + Codex's `/codex:review` output
**Outputs**: `docs/code_reviews/YYYY-MM-DD-{name}.md`
**Token**: ~5-12K Claude-side (Codex usage is separate)
**Composition**:
- PASS → `code-commit`
- FAIL → surface to user, no automatic chaining
- Codex unavailable → proceed with Review A only, alert user
