# Skills — Runtime-Specific Single-Model Manifests + TD-NL Evolution

This directory holds the SER framework's skills for two independent
single-model runtimes. Each skill directory contains a runtime-neutral
`SKILL.md`, runtime-native manifests, or both. The installer selects the
manifest for the active runtime and exposes it as the installed `SKILL.md`.

## How skills are organized

```
skills/
  {skill-name}/              # 27 core + 11 bundled auxiliary/specialist skills
    SKILL.md                 # runtime-neutral manifest, when applicable
    SKILL.claude.md          # Claude-native manifest, when applicable
    SKILL.openai.md          # Codex-native manifest, when applicable
  _shared/*.md               # Cross-cutting reference docs (not skills themselves)
  external/{name}/SKILL.md   # External skills (git submodules)
  td-nl/                     # Skill evolution infrastructure
```

`_shared/` holds large cross-cutting documents that multiple skills depend on:
`checklist-engine.md`, `memory-tiers.md`, `evolve-cycle.md`, and
`git-conventions.md`. Skills read them on demand. `_shared/` has no skill
manifest, so it is ignored by `scripts/install-skills.sh`.

## Skill index (27 core SER + 11 bundled auxiliary/specialist + 1 external)

A fresh unfiltered installation materializes 39 skill directories. The
sections below index the 27 core SER skills. The 11 bundled directories not
counted as core are the `peer-review` coordinator; the nine specialists
`peer-review-correctness`, `peer-review-critique`,
`peer-review-evaluations`, `peer-review-for-ddl`,
`peer-review-presentation`, `peer-review-qa`, `peer-review-sac`,
`peer-review-significance`, and `peer-review-story`; and the special-purpose
`play-tic-tac-toe` skill. The external `fey-r` directory brings the installed
total to 39.

### Session lifecycle
- `session-open` (formats the SessionStart hook's deterministic context — `scripts/session_context.sh`)
- `session-close` (evidence-first: RESEARCH_STATE.md + EXPERIMENTS.json; digest optional)

### Paper reading
- `paper-lit-search` (discovery — arXiv + Semantic Scholar + local)
- `paper-read` — reading (Standard triage or Deep/Fey-R) + COMPARE + INDEX modes (absorbed `paper-compare`/`paper-index`, 2026-07-13)
- `external/fey-r` — deep Feynman-method paper reading
- Chain: `paper-lit-search → paper-read`

### Paper figures & build
- `paper-assets` — one mode-based skill: ILLUSTRATE / FIGURE / ART / COMPILE (absorbed `paper-illustrate/figure/art/compile`, 2026-07-13); the deterministic LaTeX build lives in `scripts/compile_paper.sh`

### Theory & proofs
- `theory` — modes: FORMALIZE / DECOMPOSE / SEARCH / COUNTEREXAMPLE / GENERALIZE (absorbed the 5 `theory-*` skills, 2026-07-13)
- `proof` — modes: WRITE / CRITIQUE / FIX / FORMALIZE / VERIFY (absorbed the 5 `proof-*` skills, 2026-07-13)
- Chain: `theory` → `proof` (write → critique → fix → formalize)

### Writing
- `writing` — modes: OUTLINE / DRAFT / POLISH (absorbed `writing-outline/draft/polish`, 2026-07-13)
- `writing-review` — separate skill; the active runtime directly executes its native manifest

### Planning & progress
- `plan-suggest` (SELECT stage; + MILESTONE mode, absorbed `plan-milestone` 2026-07-13)
- `decision-analyze` (+ CONVERGE mode, absorbed `design-converge` 2026-07-13)
- `experiment-analyze` (EVALUATE stage)
- Status reporting is NOT a skill: `python -m harness status` (absorbed `status-report` + `checklist-status`, 2026-07-13); progress reports → `checklist` update mode (absorbed `progress-capture`, 2026-07-13)

### Experiments
- `experiment-plan` (design phase: claims / variables / baselines / ablations / **pre-registered contracts** → ledger)
- `experiment-dse` (hyperparameter sweep over a plan)
- `experiment-run` — judgment only (contract gate, GPU choice); dispatch mechanics migrated to `python -m harness ext-launch` (2026-07-13); SER-repo experiments use `python -m harness run`
- `experiment-monitor` — thin wrapper over `python -m harness ext-status` (deterministic polling migrated to harness, 2026-07-13)
- `experiment-analyze` (EVALUATE stage: verdict vs the pre-registered contract → RESEARCH_STATE.md evidence)
- Chain: `experiment-plan → experiment-dse → experiment-run → experiment-monitor → experiment-analyze`
- An experiment is complete only after `experiment-analyze` — "launched"/"finished" are not results

### Ideas
- `idea` — modes: EXPLORE / DISCOVER / REFINE (absorbed `research-explore` + `idea-discover` + `idea-refine`, 2026-07-13)
- `idea-verify` — separate skill; the active runtime directly executes its native manifest
- Chain: `idea` (discover) → `idea-verify` → `idea` (refine) → `experiment-plan`

### Checklist engine
- `checklist` — one mode-based skill: CREATE / UPDATE / VERIFY / RECOUNT (absorbed `checklist-create/update/verify/status`, 2026-07-13; read-only reporting → `python -m harness status`)
- Shared vocabulary: `_shared/checklist-engine.md`

### Memory
- `memory` — one mode-based skill: WRITE / RETRIEVE / CONSOLIDATE / FORGET (absorbed `memory-write/retrieve/consolidate/forget`, 2026-07-13)
- Shared vocabulary: `_shared/memory-tiers.md`

### Code family
- `code` — one mode-based skill: BRANCH / ROADMAP / DEBUG / COMMIT (absorbed `code-branch/roadmap/debug/commit`, 2026-07-13)
- `code-implement`, `code-review` — separate skills; the active runtime directly executes their native manifests
- Shared vocabulary: `_shared/git-conventions.md`

### Runtime manifests

- `--runtime claude` is the default. It selects `SKILL.claude.md`, then
  falls back to runtime-neutral `SKILL.md`, and installs into
  `.claude/skills/`.
- `--runtime codex` selects `SKILL.openai.md`, then falls back to
  runtime-neutral `SKILL.md`, and installs materialized copies into
  `.agents/skills/`.
- `code-implement`, `code-review`, `writing-review`, and `idea-verify` stay
  standalone because each has an independent responsibility and a direct
  manifest for both runtimes.
- Runtime-native manifests are materialized as installed `SKILL.md` files.
  Claude `--link` can link only neutral manifests; Codex installs are always
  materialized copies.

### Meta (skill evolution)
- `skill-feedback` (signal-gated online EWMA Q update after real reward),
  `evolve-suggest` (explicit audit or session-close opt-in; pending flags,
  derived V^L, optional proposal), `evolve-apply` (user-approved proposal
  with version archive + rollback)
- (fallback skill `general-research` retired 2026-07-13 — unmatched research requests are handled directly under CLAUDE.md)
- Shared vocabulary: `_shared/evolve-cycle.md`.

### Integration (one-off)
- `project-integrate` — merge an unpacked SER distribution into an existing project

## Install for a runtime

Run `bash scripts/install-skills.sh --list` to list everything discovered,
`bash scripts/install-skills.sh` to copy into `./.claude/skills/`, or
`bash scripts/install-skills.sh --link --force` for a developer-friendly
Claude install. Use `bash scripts/install-skills.sh --runtime codex` to
materialize the Codex surface in `./.agents/skills/`.

## TD-NL evolution infrastructure

```
td-nl/
  feedback-log.md       # pending/processed flags + pending proposals
  value-function.md     # V^L derived on demand from active Q^L values
  skill-values/         # Q^L per skill, updated only after real reward
    _template.md        # Template for new skill value files
  history/              # Spec version archive (pre-edit snapshots for rollback)
```

The canonical flow is: real reward signal → signal-gated `skill-feedback` →
online EWMA Q update and optional flag; explicit audit or session-close opt-in
→ `evolve-suggest` over pending flags and derived V^L; user approval →
`evolve-apply`. See `_shared/evolve-cycle.md` for the gates and rollback rules.

## External skills (git submodules)

| Directory | Skill | Purpose |
|-----------|-------|---------|
| `external/fey-r/` | `fey-r` | Feynman-method paper reading (deep understanding via derivation) |

Run `git submodule update --init --recursive` or `bash scripts/setup.sh` to initialize.
