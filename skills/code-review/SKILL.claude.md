---
name: code-review
description: Review code changes after `code-implement` completes. For roadmap-driven (medium/large) tasks, verifies plan compliance — Done Criteria, per-step Acceptance, Constraints violations, Unplanned changes. For small tasks, performs a quick check (diff read + tests pass + change matches user intent). Produces `docs/code_reviews/{name}.md`. Triggers after `code-implement` or when user asks "review these changes", "check the implementation".
---

# code-review (Track A — Claude single-reviewer)

**Trigger**: Code changes are ready for review after `code-implement` completes (small or medium/large), before commit.

**Shared context**: None (Track A). The roadmap file — if present — carries the spec to check against.

**Track**: A. Installed via `--codex-track claude`. Track B installs a dual-reviewer variant that adds Codex as a second independent reviewer.

---

## Step 1 — Determine mode

| Source of changes | Mode |
|-------------------|------|
| Small task (no roadmap) | **Quick check** (Step 2) |
| Medium/Large task with roadmap | **Full review** against the roadmap (Step 3) |

---

## Step 2 — Quick check (small tasks)

1. Read `git diff` against the working tree.
2. Run the relevant test file / test command. Record pass/fail.
3. Compare: does the change do what the user asked? (Re-read the original request.)
4. Flag any obvious issues: unintended file modifications, dead code, missing edge cases.

### Output

```markdown
## Quick Review

**Change scope**: {files modified}
**Tests**: {PASS / FAIL with details}
**Matches user request**: {yes / partial — {what's off}}
**Issues**: {none, or bulleted list}
**Assessment**: {PASS — ready for commit / FAIL — fix first}
```

Save to `docs/code_reviews/quick-YYYY-MM-DD-{short-name}.md` only if the task is non-trivial enough to merit a record; otherwise emit to console.

---

## Step 3 — Full review (roadmap-driven tasks)

### Inputs

1. Roadmap file: `docs/implement_roadmap/YYYY-MM-DD-{name}.md`.
2. Changes since execution started:
   - `git diff {base_commit_sha}` — modifications to tracked files (use the SHA from the roadmap Status `Base commit:` field).
   - `git status -s` — new/untracked files (diff does not show these).
3. Test results from running the roadmap's Test command and each Done Criterion.

### Process

1. **Run Done Criteria**: for each criterion in the roadmap, run the command. Record PASS or FAIL with evidence.
2. **Per-step verification**: for each step, compare the diff against the step's Files + What to do + Acceptance:
   - Does the diff contain the expected changes for this step?
   - Were the specified files created / modified?
   - Any unexpected deletions or modifications?
3. **Constraint compliance**: check each entry in the roadmap's Constraints section:
   - Were any forbidden files modified (`.claude/`, `skills/`, etc.)?
   - Were any unplanned dependencies added?
   - Were files outside the roadmap scope modified? If yes, was it justified in the step descriptions?
4. **Goal check**: does the total change, read as a whole, achieve what the Goal line of the roadmap promises?

### Output

Save to `docs/code_reviews/YYYY-MM-DD-{roadmap-name}.md`:

```markdown
# Code Review — {Roadmap Name}

**Roadmap**: `docs/implement_roadmap/{path}`
**Base commit**: {SHA}
**Test suite**: {PASS / FAIL with details}
**Reviewer**: Claude (Track A)

## Done Criteria
- [x] {criterion 1} — PASS
- [ ] {criterion 2} — FAIL: {what went wrong}

## Per-Step Verification

| Step | Title | Acceptance | Status | Notes |
|------|-------|------------|--------|-------|
| 1 | {title} | {criterion} | PASS | — |
| 2 | {title} | {criterion} | FAIL | {what's wrong} |

## Constraint Violations
- {none, or list violations}

## Unplanned Changes
- {files modified outside roadmap scope, with assessment: justified / concerning}

## Overall Assessment

{PASS — ready for commit / FAIL — issues listed above need fixing}
```

---

## Step 4 — Deliver the verdict

- **PASS** → suggest `code` (commit mode).
- **FAIL** → surface the report to the user. Do NOT auto-loop back to `code-implement` (SER has no automatic fix cycle). User decides next action: manual fix, re-run `code-implement`, redesign roadmap, or commit with known issues.

---

## Architectural Note

Track A uses a single reviewer (Claude main session) against the roadmap. Claude's role is **plan compliance** — does the implementation actually achieve the research goal the roadmap stated.

Track B adds a second independent reviewer (`/codex:review`) whose role is **code quality** — logic, edge cases, security, maintainability. The two roles do not overlap. Track A loses the second perspective; Track A users who want code-quality review must run it manually via external tools.

---

## Output

```
[code-review / claude] Review complete — {PASS | FAIL}
  Mode: {quick | full}
  Report: {docs/code_reviews/... | console}
  Next: the code skill's commit mode (if PASS) or user decision (if FAIL)
```

**Inputs**: `git diff {base_sha}` + `git status` + roadmap file (if any) + test command output
**Outputs**: `docs/code_reviews/YYYY-MM-DD-{name}.md` (full mode) or console (quick mode)
**Token**: ~3-8K
**Composition**:
- PASS → `code` (commit mode)
- FAIL → surface to user, no automatic chaining
