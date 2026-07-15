---
name: code-review
description: Use when code changes are ready for review before commit, after implementation completes, or when the user asks to inspect a diff for correctness and scope.
---

# code-review

**Trigger**: Code changes are ready for review after `code-implement`, before commit, or the user asks for a review.

**Runtime**: The active Codex session performs the review directly.

---

## Step 1 — Determine Mode

| Source of changes | Mode |
|-------------------|------|
| Small task without a roadmap | **Quick check** (Step 2) |
| Medium/Large task with a roadmap | **Full review** (Step 3) |

---

## Step 2 — Quick Check

1. Read the complete working-tree diff, including untracked files in scope.
2. Run the relevant test command and record its result.
3. Compare the implementation with the user's request.
4. Flag unintended changes, dead code, missing edge cases, security risks, and unsupported claims.

### Output

```markdown
## Quick Review

**Change scope**: {files modified}
**Tests**: {PASS / FAIL with details}
**Matches user request**: {yes / partial — explanation}
**Issues**: {none or a prioritized list}
**Assessment**: {PASS — ready for commit / FAIL — fix first}
```

Save a report to `docs/code_reviews/quick-YYYY-MM-DD-{short-name}.md` only when a durable record is useful; otherwise report inline.

---

## Step 3 — Full Review

### Inputs

1. `docs/implement_roadmap/YYYY-MM-DD-{name}.md`
2. `git diff {base_commit_sha}` using the SHA recorded in the roadmap
3. `git status --short` for untracked and other working-tree changes
4. Fresh results from the roadmap's tests and Done Criteria

### Process

1. **Run Done Criteria**: execute each criterion and record PASS or FAIL with evidence.
2. **Verify each step**: compare the diff with the step's Files, What to do, and Acceptance sections.
3. **Check constraints**: identify forbidden files, new dependencies, or changes outside authorized scope.
4. **Review code quality**: inspect logic, edge cases, error handling, security, maintainability, and test adequacy.
5. **Check the goal**: determine whether the complete change achieves the roadmap's stated goal.

### Output

Save `docs/code_reviews/YYYY-MM-DD-{roadmap-name}.md`:

```markdown
# Code Review — {Roadmap Name}

**Roadmap**: `docs/implement_roadmap/{path}`
**Base commit**: {SHA}
**Test suite**: {PASS / FAIL with details}
**Reviewer**: active Codex session

## Done Criteria
- [x] {criterion} — PASS
- [ ] {criterion} — FAIL: {evidence}

## Per-Step Verification

| Step | Title | Acceptance | Status | Notes |
|------|-------|------------|--------|-------|
| 1 | {title} | {criterion} | PASS | — |

## Code Quality Findings
- {none or prioritized findings with file and line evidence}

## Constraint Violations
- {none or list}

## Unplanned Changes
- {none or files with assessment}

## Overall Assessment

{PASS — ready for commit / FAIL — fixes required}
```

---

## Step 4 — Deliver the Verdict

- **PASS** → suggest `code` (COMMIT mode).
- **FAIL** → report the findings and stop. The user decides whether to fix, redesign, or accept known issues.

Do not modify reviewed code unless the user also authorizes implementation.

---

## Output

```text
[code-review / codex] Review complete — {PASS | FAIL}
  Mode: {quick | full}
  Report: {path | inline}
  Next: code (COMMIT mode) if PASS, otherwise user decision
```

**Inputs**: Diff, status, roadmap when present, and fresh test evidence

**Outputs**: Review report or inline verdict
