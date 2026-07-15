# Upstream v6 and Codex Runtime Integration Design

## Goal

Starting from local `main` at `9333b82`, incorporate every commit reachable from
`upstream/main` at `89425b9` while preserving the local Codex-native runtime.
The resulting `main` must contain `upstream/main` in its ancestry and expose one
coherent v6 skill architecture to both Claude and Codex.

The result is intentionally not byte-for-byte identical to upstream. It is the
upstream v6 framework plus the maintained Codex runtime layer.

## Non-goals

- Do not reset or rebase the published `main` history.
- Do not discard the 24 local Codex-runtime commits.
- Do not retain legacy Codex-only skills merely because Git can preserve them.
- Do not modify or delete the existing untracked project files (`config.yaml`,
  `docs/.gitkeep`, `memory/td-nl/`, and `papers/`).
- Do not push to either remote as part of this integration unless separately
  requested.

## Integration strategy

Create an isolated branch from the current local `main`, then merge
`upstream/main` with a merge commit. This preserves both published histories and
avoids the force-push requirement of rebasing local `main`.

Resolve the known overlaps as follows:

1. `CLAUDE.md`: take the upstream v6 evidence-loop protocol as the canonical
   Claude protocol. Preserve local material only where it remains accurate for
   the new architecture.
2. `README.md`: use the upstream consolidated-skill documentation and retain a
   corrected Codex-native runtime section.
3. `skills/play-tic-tac-toe/SKILL.md`: use the upstream single-move contract
   because the new harness and smoke experiment depend on its strict output.
4. `skills/idea-refine/SKILL.md`: accept upstream consolidation and deletion;
   migrate any still-needed Codex behavior into `skills/idea/` rather than
   keeping a legacy duplicate.

## Codex protocol migration

`AGENTS.md` is the Codex counterpart of the upstream root protocol. It will be
updated from the old checklist-first v5 description to the v6 evidence-loop
model while retaining Codex-specific runtime rules:

- `.agents/skills/` remains the installed skill location.
- `AGENTS.md`, not `CLAUDE.md`, is the Codex behavioral entry point.
- No Claude Code delegation commands, Claude-only hooks, or cross-model Codex
  delegation are required by the Codex runtime.
- Scientific state, experiment ledger, run artifacts, durable context,
  checklists, and idea backlog keep the same ownership boundaries as upstream.
- Experiment contracts and evidence guardrails apply equally in Codex.

The Codex protocol does not need to duplicate every explanatory paragraph in
`CLAUDE.md`; it must preserve all enforceable routing, state-ownership, and
experiment-safety requirements.

## Skill architecture migration

Upstream consolidates the old micro-skills into larger mode-based skills. The
Codex installation must follow that architecture instead of installing a hybrid
of new aggregate skills and old Codex-only variants.

For every source skill discovered by `scripts/install-skills.sh`:

- Prefer `SKILL.openai.md` when a genuine Codex-specific implementation is
  necessary.
- Otherwise allow a runtime-neutral `SKILL.md` only when it contains no
  Claude-only paths or instructions.
- Port protocol references from `CLAUDE.md` to runtime-neutral wording or a
  Codex variant where needed.
- Remove or stop discovering obsolete `SKILL.openai.md` files whose skill was
  consolidated upstream.
- Ensure one intent family maps to one installed Codex skill unless upstream
  deliberately retains a compatibility shim.

The installer audit remains strict: a Codex-installed manifest must not depend
on `.claude/`, `CLAUDE.md`, `Claude Code`, `/codex:*`, or
`mcp__codex__codex`.

## Tests and migration gates

Tests will be added before installer or runtime behavior is changed. They must
demonstrate these requirements:

1. A Codex dry-run/install can traverse every consolidated upstream skill
   without forbidden runtime coupling.
2. The installed Codex skill inventory does not contain obsolete duplicates
   from the pre-consolidation architecture.
3. The Codex root protocol contains the v6 state and contract invariants.
4. Existing Claude installation behavior remains supported.

The integration is acceptable only when all of the following pass from the
merged tree:

- `bash scripts/test_install_skills.sh`
- the repository Python test suite
- `python -m harness smoke-test`
- Codex runtime installation into a temporary target
- forbidden-marker and duplicate-inventory checks on that target
- `git merge-base --is-ancestor upstream/main HEAD`

## Completion and branch handling

After the integration branch passes all gates, fast-forward local `main` to the
validated integration branch. Keep `origin/main` unchanged unless the user later
requests a push. The final handoff must report the merge commit, exact tests and
counts, remaining untracked files, and local-vs-origin/upstream ahead/behind
status.
