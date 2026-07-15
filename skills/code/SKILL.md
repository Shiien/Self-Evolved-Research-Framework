---
name: code
description: Code-workflow scaffolding in one mode-based skill — BRANCH (git branch/worktree isolation with exp|feat|fix prefixes), ROADMAP (step-by-step implementation roadmap saved to docs/implement_roadmap/ that code-implement executes), DEBUG (rigid four-phase Reproduce → Isolate → Root Cause → Verify, with the three-failed-fixes-means-architecture rule), COMMIT (pre-commit verification, prefixed message, explicit staging, checklist SHA annotation). Absorbs the former code-branch / code-roadmap / code-debug / code-commit skills — those names now refer to modes here. Implementation and review stay separate skills (`code-implement`, `code-review`; codex-track variants). Triggers on "start a branch", "create a worktree", "write the implementation roadmap", "debug this", "test fails", "commit these changes".
---

# code

Writing the code is `code-implement`; reviewing it is `code-review` (both
ship codex-track variants). Chain: BRANCH → ROADMAP → `code-implement` →
DEBUG (as needed) → `code-review` → COMMIT.

**Shared context**: Read `skills/_shared/git-conventions.md` for branch
naming, worktree pattern, commit prefixes, staging rules, and the
never-commit list — the modes below don't restate them.

## Mode: BRANCH — "start a branch", "isolate this work"

| Signal | Path |
|---|---|
| Small edit (<30 lines, single file, <1h) | stay on current branch — report and skip |
| New feature / multi-file change | `git checkout -b {exp|feat|fix}/{slug}` |
| Long-running or must-not-disturb work | `git worktree add .worktrees/{type}-{slug} -b {type}/{slug}` then work there |
| Experiment sweep / ablation / probe | named `exp/*` branch |

Report the branch/worktree to the user and to downstream modes.

## Mode: ROADMAP — medium/large task needs a plan before code

1. Understand the goal (ask if ambiguous), read the relevant sources and
   `methodology/approach.md`, identify the test framework + exact test
   command.
2. Save `docs/implement_roadmap/YYYY-MM-DD-{name}.md` — **every section
   mandatory** (this format is the execution contract `code-implement`
   Track A/B both consume):
   - `## Goal` — one sentence, end state.
   - `## Context` — project, language/framework, **test command verbatim**,
     key files with one-line whys.
   - `## Constraints` — never modify `.claude/`, `skills/`, `memory/`,
     `hooks/`, `config.yaml`, `CLAUDE.md`; no `git commit/push` during
     execution; no new deps unless justified in a step; + project-specific.
   - `## Steps` (3-8; fewer → maybe no roadmap needed, more → split): each
     step has **Purpose / Files (Create·Modify·Test) / What to do**
     (function-class level, describe not code) **/ Acceptance** (runnable
     command or verifiable condition).
   - `## Done Criteria` — full test suite + functional check + regression
     check.
   - `## Status` — one checkbox per step, base commit, last updated.
3. Quality check before presenting: acceptance runnable, key files exist,
   constraints include framework dirs, test command verbatim.
4. Driven by a checklist Implementation checkbox → append the roadmap path
   as its artifact (`checklist` update mode).

## Mode: DEBUG — any bug, test failure, unexpected behavior (RIGID phases)

1. **Reproduce** — run the exact failing command yourself; never trust
   second-hand descriptions; establish the failure rate if flaky.
2. **Isolate** — binary-search the smallest failing unit; check
   `git diff` / `git log` (bisect if it used to work); targeted assertions,
   not print-spray.
3. **Root cause** — the cause, not the symptom. **Hard rule: three failed
   fix attempts in a row → STOP**, report the three hypotheses and why each
   failed, and raise "this is architectural, not implementation" to the
   user. Do not attempt fix 4.
4. **Verify** — fix addresses the root cause; original failing command
   passes; full suite passes; temporary debug code removed. → `code-review`
   → COMMIT with `fix:`.

## Mode: COMMIT — after `code-review` passes

1. **Pre-commit verification**: full test command (from the roadmap
   Context) passes; each Done Criterion checked with evidence;
   `git diff --stat` presented; explicit user confirmation ("Proceed?
   y/n" — never commit on ambiguity). Small no-roadmap tasks keep the diff
   summary + confirmation only.
2. Prefix by dominant intent: `feat: | fix: | exp: | refactor: | docs: |
   chore:` — imperative subject ≤72 chars; body explains WHY.
3. Stage **explicitly by filename** (never `-A`); `git status` against the
   never-commit list.
4. Post-commit: tree clean, `git log -1` sane, capture the SHA.
5. Checklist-driven tasks → `checklist` (update mode): mark `[x]` and
   annotate the checkbox with the roadmap path + short SHA. Push is
   separate, per git-conventions.

**Inputs**: task intent / failing output / reviewed tree
**Outputs**: branch·worktree / `docs/implement_roadmap/*.md` / fixed code / commit
**Token**: BRANCH 1-2K · ROADMAP 3-8K · DEBUG 3-15K · COMMIT 2-5K
**Composition**: ROADMAP → `code-implement`; DEBUG fix needing real logic →
`code-implement` TDD loop then back to phase 4; COMMIT ← `code-review` PASS.
