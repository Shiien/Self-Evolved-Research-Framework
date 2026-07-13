# Skills — Standard Claude Code Skills + TD-NL Evolution

This directory holds the SER framework's skills in **standard Claude Code format**:
one directory per skill, each with a `SKILL.md` that has YAML frontmatter
(`name`, `description`) and a markdown body. Claude Code auto-loads the body
when a skill's description matches the current conversation intent.

## How skills are organized

```
skills/
  {skill-name}/SKILL.md      # 32 SER skills (Phase 3 consolidation in progress — see REFACTOR_PLAN.md §7)
  _shared/*.md               # Cross-cutting reference docs (not skills themselves)
  external/{name}/SKILL.md   # External skills (git submodules)
  td-nl/                     # Skill evolution infrastructure
```

`_shared/` holds large cross-cutting documents that multiple skills depend on:
`checklist-engine.md`, `memory-tiers.md`, `evolve-cycle.md`. The skills that
need them instruct Claude to Read them on demand. `_shared/` has no `SKILL.md`
so it's ignored by `scripts/install-skills.sh`.

## Skill index (32 SER + 1 external)

### Session lifecycle
- `session-open` (formats the SessionStart hook's deterministic context — `scripts/session_context.sh`)
- `session-close` (evidence-first: RESEARCH_STATE.md + EXPERIMENTS.json; digest optional)

### Paper reading
- `paper-lit-search` (discovery — arXiv + Semantic Scholar + local)
- `paper-read` — reading (Standard triage or Deep/Fey-R) + COMPARE + INDEX modes (absorbed `paper-compare`/`paper-index`, 2026-07-13)
- `external/fey-r` — deep Feynman-method paper reading
- Chain: `paper-lit-search → paper-read`

### Paper figures & build
- `paper-illustrate` — structural diagrams (architecture, pipeline, flow) via TikZ or SVG
- `paper-figure` — data-driven plots (line, bar, scatter, heatmap, table) from experiment results; script preserved under `paper/figures/scripts/`
- `paper-art` — decorative / identity visuals (pixel art, project mascot, README hero); saved to `outputs/visuals/`
- `paper-compile` — full LaTeX build pipeline (pdflatex×3 + bibtex/biber) with pre-compile integrity checks

### Theory & proofs
- `theory` — modes: FORMALIZE / DECOMPOSE / SEARCH / COUNTEREXAMPLE / GENERALIZE (absorbed the 5 `theory-*` skills, 2026-07-13)
- `proof` — modes: WRITE / CRITIQUE / FIX / FORMALIZE / VERIFY (absorbed the 5 `proof-*` skills, 2026-07-13)
- Chain: `theory` → `proof` (write → critique → fix → formalize)

### Writing
- `writing` — modes: OUTLINE / DRAFT / POLISH (absorbed `writing-outline/draft/polish`, 2026-07-13)
- `writing-review` — separate skill (ships codex-track variants)

### Planning & progress
- `plan-suggest` (SELECT stage; + MILESTONE mode, absorbed `plan-milestone` 2026-07-13)
- `decision-analyze` (+ CONVERGE mode, absorbed `design-converge` 2026-07-13)
- `experiment-analyze` (EVALUATE stage)
- Status reporting is NOT a skill: `python -m harness status` (absorbed `status-report` + `checklist-status`, 2026-07-13); progress reports → `checklist` update mode (absorbed `progress-capture`, 2026-07-13)

### Experiments
- `experiment-plan` (design phase: claims / variables / baselines / ablations / **pre-registered contracts** → ledger)
- `experiment-dse` (hyperparameter sweep over a plan)
- `experiment-run` (contract-gated launch; SER-repo experiments delegate to `python -m harness run`)
- `experiment-monitor` — thin wrapper over `python -m harness ext-status` (deterministic polling migrated to harness, 2026-07-13)
- `experiment-analyze` (EVALUATE stage: verdict vs the pre-registered contract → RESEARCH_STATE.md evidence)
- Chain: `experiment-plan → experiment-dse → experiment-run → experiment-monitor → experiment-analyze`
- An experiment is complete only after `experiment-analyze` — "launched"/"finished" are not results

### Ideas
- `idea` — modes: EXPLORE / DISCOVER / REFINE (absorbed `research-explore` + `idea-discover` + `idea-refine`, 2026-07-13)
- `idea-verify` — separate skill (ships codex-track variants)
- Chain: `idea` (discover) → `idea-verify` → `idea` (refine) → `experiment-plan`

### Checklist engine
- `checklist` — one mode-based skill: CREATE / UPDATE / VERIFY / RECOUNT (absorbed `checklist-create/update/verify/status`, 2026-07-13; read-only reporting → `python -m harness status`)
- Shared vocabulary: `_shared/checklist-engine.md`

### Memory
- `memory` — one mode-based skill: WRITE / RETRIEVE / CONSOLIDATE / FORGET (absorbed `memory-write/retrieve/consolidate/forget`, 2026-07-13)
- Shared vocabulary: `_shared/memory-tiers.md`

### Code family
- `code-branch`, `code-roadmap`, `code-implement`, `code-review`, `code-debug`, `code-commit`
- Shared vocabulary: `_shared/git-conventions.md` (all tracks) and `_shared/codex-contract.md` (codex track only)

### Codex track (cross-cutting)
- Flag: `scripts/install-skills.sh --codex-track claude|codex` (default `claude`)
- Skills shipping `SKILL.claude.md` + `SKILL.codex.md` variants (installer materializes the selected one as `SKILL.md`):
  - `code-implement` — Track B delegates medium/large tasks to `/codex:rescue`
  - `code-review` — Track B adds `/codex:review` as a second technical reviewer
  - `writing-review` — Track B adds a 3rd Codex peer reviewer (ADD mode, max_rounds 4→3)
  - `idea-verify` — Track B adds a 4th evidence source via `mcp__codex__codex` (post-Claude-cutoff prior work)
- Shared vocabulary: `_shared/cross-model-review.md` (writing-review, idea-verify; codex track only)
- `codex` track preflight strictly verifies `/codex:setup`, Superpowers, `/codex:review`, and `mcp__codex__codex` MCP registration

### Meta (skill evolution)
- `skill-feedback` (online per-firing Q-update, signal-gated), `evolve-suggest` (on-demand audit + proposal), `evolve-apply` (commit proposal with version archive + rollback)
- (fallback skill `general-research` retired 2026-07-13 — unmatched research requests are handled directly under CLAUDE.md)
- Shared vocabulary: `_shared/evolve-cycle.md`. Replaces the deprecated v3 batch G2→G1 + TextGrad pipeline.

### Integration (one-off)
- `project-integrate` — merge an unpacked SER distribution into an existing project

## Install into `.claude/skills/`

Run `bash scripts/install-skills.sh --list` to list everything discovered,
`bash scripts/install-skills.sh` to copy into `./.claude/skills/`, or
`bash scripts/install-skills.sh --link --force` for a developer-friendly
symlinked install.

## TD-NL evolution infrastructure

```
td-nl/
  feedback-log.md       # G2 entries (per-firing) + processed cycles
  value-function.md     # V^L: global skill system assessment
  skill-values/         # Q^L per skill (created on first firing)
    _template.md        # Template for new skill value files
  history/              # Spec version archive (pre-edit snapshots for rollback)
```

See `_shared/evolve-cycle.md` for the full G2 → G1 → `evolve-suggest` → `evolve-apply` process.

## External skills (git submodules)

| Directory | Skill | Purpose |
|-----------|-------|---------|
| `external/fey-r/` | `fey-r` | Feynman-method paper reading (deep understanding via derivation) |

Run `git submodule update --init --recursive` or `bash scripts/setup.sh` to initialize.
