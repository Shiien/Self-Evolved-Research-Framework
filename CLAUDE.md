# SER v5.0 — Behavioral Protocol

> Self-Evolved Research: A behavior-driven research collaboration framework.
> All skills trigger automatically via intent detection — no explicit commands needed.

> **Self-Evolving Principle**: The framework improves its own micro-skills through use.
> When a SER skill firing has an actual reward signal — explicit user feedback,
> downstream consumption, or hard failure — `skill-feedback` updates that skill's
> Q^L online (EWMA-with-anchor, signal-gated). Audit and spec-edit proposals are
> on-demand via `evolve-suggest`. The dead "G2 every firing → G1 batch" pipeline
> is deprecated; the skills you use today become better tomorrow only when there
> is real signal to learn from.

## Enforcement Priority

**ABSOLUTE RULE — SESSION-OPEN FIRST**: At conversation start, `session-open` MUST
execute BEFORE any other processing, skill evaluation, or response — including
clarifying questions, brainstorming checks, or external skill hooks. No exceptions.

SER micro-skills take precedence over external skill systems for research tasks.
External skills (brainstorming, claudeception) remain active for their domains
but do NOT override SER intent routing.

## Session Protocol

### Conversation Start → `session-open`

At the start of each conversation, **silently execute** the following steps, then output a status banner:

1. Read: `config.yaml` + the most recent `logs/digest/*.yaml` + `logs/digest/SUMMARY.md`
2. Read: `memory/MEMORY.md` (always-loaded memory index)
3. Execute `memory-retrieve`: load active context and relevant memories
4. Read: `Checklist.md` (project progress root)
5. Output:
   ```
   [SER] {project_name} | Phase {X} | [{done}/{total} items] | V^L={overall}/10
   Last session ({date}): {1-line summary}
   Next milestone: {goal} ({days}d)
   ```
6. If milestone ≤3 days away: append `** MILESTONE APPROACHING **`
7. Proceed directly to the user's request without asking questions

### During Session → Online Q-update via `skill-feedback`

After a SER micro-skill fires, invoke `skill-feedback` **only when a usable
reward signal exists**:

1. Explicit user feedback in the messages following the firing (correction,
   acceptance, rejection),
2. Downstream consumption (a later skill read the output, used the file,
   chained from it — or had to retry it), OR
3. Hard failure (no output, error, schema-invalid artifact).

Self-assessed "I think this was fine" is **not** a signal. Skip silently.
See `skills/_shared/evolve-cycle.md` for the full spec. Cost: ~80-150 tokens
per fire, zero when the gate rejects.

### Conversation End → `session-close`

When the conversation is about to end:
1. Generate a summary (1-3 key points + decisions + file changes). **Record all user text input.**
2. Execute `memory-write` → `memory-consolidate`
3. Update `memory/MEMORY.md`
4. Ask: "Save session log? [Y/edit]"
5. Write to `logs/digest/YYYY-MM-DD.yaml`, update `SUMMARY.md`
6. Optional: ask "Run skill audit? [y/N]" → `evolve-suggest` only if yes.
   Skill audit is no longer mandatory because per-firing Q^L updates already
   happened online via `skill-feedback`.

---

## Intent Router

Priority matches from top to bottom. Each SER skill lives in its own directory
under `skills/{skill-name}/` with a standard `SKILL.md`, so Claude Code auto-loads
the body when the skill fires; the router below describes *why* and *when* a skill
should be chosen.

| # | Detection Pattern | Skill |
|---|-------------------|-------|
| 1 | Conversation start | `session-open` |
| 2 | Conversation end | `session-close` |
| 3 | User discusses/shares a paper | `paper-read` |
| 3b | User wants to deeply study a paper ("understand", "study", "Fey-R") | `paper-read` (Deep/Fey-R mode) → `fey-r` |
| 4 | Comparing multiple papers | `paper-compare` |
| 5 | User proposes a theorem/conjecture | `theory-formalize` |
| 6 | User presents a proof draft for review | `proof-critique` |
| 7 | User requests writing a paper section | `writing-draft` |
| 8 | User asks "what to do next" | `plan-suggest` (reads the checklist tree) |
| 9 | User asks "project status" | `status-report` / `checklist-status` |
| 10 | User reports completing something | `progress-capture` |
| 11 | Complex proof decomposition needed | `theory-decompose` |
| 12 | Stuck on a proof / seeking methods | `theory-search` |
| 13 | Weighing options / making a decision | `decision-analyze` |
| 14 | Sharing experiment results | `experiment-analyze` |
| 15 | User asks to run / launch experiment | `experiment-run` |
| 16 | User asks to check experiment status | `experiment-monitor` |
| 17 | User asks to brainstorm ideas | `idea-discover` |
| 18 | User asks "is this idea novel?" | `idea-verify` |
| 19 | User asks to create a paper checklist | `checklist-create` (uses paper audit template) |
| 20 | User asks to verify paper claims | `checklist-verify` |
| 21 | Paper changed, checklist needs sync | `checklist-update` |
| 22 | Open-ended research exploration | `research-explore` |
| 23 | Architecture/design decision | `design-converge` |
| 24 | Other research-related (fallback) | `general-research` |
| 25 | User wants to add/track a task | `checklist-create` |
| 26 | User asks to start a branch / isolate work / create a worktree | `code-branch` |
| 27 | Medium/large coding task needing a plan before writing code | `code-roadmap` |
| 28 | User asks to implement / add feature / change code behavior | `code-implement` |
| 29 | Test fails / bug reported / unexpected behavior | `code-debug` |
| 30 | Review code changes after implementation | `code-review` |
| 31 | Commit reviewed code changes | `code-commit` |
| 32 | User asks for architecture/pipeline/flow diagram for a paper | `paper-illustrate` |
| 33 | User asks for pixel art / project mascot / README hero / decorative SVG | `paper-art` |
| 34 | User asks to compile the paper / build PDF / "编译论文" | `paper-compile` |
| 35 | User asks to generate a data plot / bar chart / heatmap / table — or chained after `experiment-analyze` | `paper-figure` |
| 36 | User asks to prove a theorem / proposition from scratch (no draft yet) — "prove that …", "write a proof of …", "证明" | `proof-write` |
| 37 | User asks to refine / sharpen / make concrete a rough idea — or chained after `idea-verify` | `idea-refine` |
| 38 | User asks to plan / design an experiment / "what experiments should we run" — or chained after `idea-refine` | `experiment-plan` |
| 39 | User asks to sweep / tune / explore hyperparameters / DSE / "grid search" / "超参搜索" | `experiment-dse` |
| 40 | User asks to search the literature / find papers / "arxiv search" / "related work" / "survey this topic" / "文献搜索" | `paper-lit-search` |
| 41 | A SER skill just fired AND there's a real reward signal (user feedback / downstream consumption / hard failure) | `skill-feedback` |
| 42 | User asks to audit skills / "propose any skill improvements" / "are any skills underperforming" | `evolve-suggest` |

---

## Checklist Engine

The hierarchical checklist is the single source of truth for project progress.

- **L0** (`Checklist.md`): Project root — read at every session-open
- **L1** (`checklists/{term}.md`): Short/mid/long-term phase checklists
- **L2** (`checklists/{term}/{category}-{slug}.md`): Specific task checklists

Items are Leaf (single checkable) or Branch (→ sub-checklist). Completion propagates upward.
Verification stages: `[ ]` → `[x]` (done) → `[v]` (verified) → `[U]` (user signed off).

All skills update the checklist after producing artifacts. The engine's shared
vocabulary (tree, markers, composition rules, paper audit template) lives in
`skills/_shared/checklist-engine.md`; the 4 operation skills are
`checklist-create`, `checklist-verify`, `checklist-update`, `checklist-status`.

---

## Skill Evolution (online + on-demand audit)

The framework optimizes its own micro-skill specs in two tiers:

1. **Online Q-update (`skill-feedback`)**: After a SER skill fires *and only when
   a real reward signal is present* (explicit user feedback, downstream
   consumption, or hard failure), update that skill's `Q^L` via an
   EWMA-with-anchor pull. Hard signals (|delta| ≥ 2) write a `[FLAG-HARD]`
   line to `feedback-log.md`. Cost: ~80-150 tokens per fire, **zero** when
   there is no signal.
2. **On-demand audit (`evolve-suggest`)**: Run when the user asks (or
   optionally at session-close). Recomputes `V^L` from the per-skill `Q^L`'s,
   reads `§ Pending Flags`, and — only if the signal threshold is met — drafts
   one spec-edit proposal.
3. **Apply (`evolve-apply`)**: User approves a proposal; the skill is edited
   with version archive + rollback support. A `Q^L` drop of ≥1.5 within 5
   firings post-edit auto-stages a rollback proposal.

Honesty note: the per-firing math is **not** TD(0) — there is no Markov
state-transition between skill firings. It is incremental EWMA. The deprecated
v3 "G2 every firing → G1 batch + TextGrad backward" path is documented in
`skills/_shared/evolve-cycle.md § Migration notes`.

Infrastructure lives in `skills/td-nl/`. See `skills/_shared/evolve-cycle.md`
for the full process.

---

## Data Contracts

### Log Format: `logs/digest/YYYY-MM-DD.yaml`

```yaml
date: "YYYY-MM-DD"
type: "session"          # session | progress | review
summary: "{1-line}"
accomplishments:
  - type: "{paper_read|experiment|proof|code|decision}"
    content: "{description}"
decisions: []
files_changed: []
token_estimate: N
milestone_phase: "{phase}"
```

### Paper Notes: `resources/papers/{ID}.md`

```yaml
---
title: "{title}"
authors: ["{author}"]
year: YYYY
venue: "{venue}"
relevance: "{high|medium|low}"
tags: []
read_date: "YYYY-MM-DD"
---
```

**Structure**: Quick Reference (first) → Background, Pain Points, Method, Experiments, Conclusion, Questions, Personal Notes.

**Reading rule**: Read only Quick Reference first. Only read the full document if deeper understanding is needed.

### Checklist Items

Leaf: `- [ ] {description}`
Branch: `- [3/7] {description} → checklists/{path}.md`
With artifact: `- [x] {description} | artifact: outputs/{path}`

### Memory System: `memory/`

Three-tier persistent memory. See `memory/CLAUDE.md` for structure and capacity limits.
See `skills/_shared/memory-tiers.md` for tier definitions; the 4 operation skills
are `memory-write`, `memory-retrieve`, `memory-consolidate`, `memory-forget`.

---

## Project Architecture

```
├── CLAUDE.md              # Behavioral protocol (this file)
├── Checklist.md           # Project progress root (L0)
├── checklists/            # Hierarchical task tracking
│   ├── short-term.md      # L1 phase checklists
│   ├── mid-term.md
│   ├── long-term.md
│   └── {term}/{cat}-{slug}.md  # L2 specific tasks
├── config.template.yaml   # Copy to config.yaml and customize
├── README.md / LICENSE
├── skills/
│   ├── CLAUDE.md          # Skill index
│   ├── {skill-name}/      # 57 SER skills, each with SKILL.md + YAML frontmatter
│   │   └── SKILL.md       # Auto-loaded by Claude Code when the skill fires
│   ├── _shared/           # Cross-cutting infra read by related skills
│   │   ├── checklist-engine.md
│   │   ├── memory-tiers.md
│   │   ├── evolve-cycle.md
│   │   ├── codex-contract.md       # Codex-track prompt contract (code-implement/review)
│   │   ├── cross-model-review.md   # MCP invocation + 4-source synthesis (writing-review / idea-verify)
│   │   └── git-conventions.md
│   ├── external/          # External skills (git submodules)
│   │   └── fey-r/         # Feynman-method paper reading
│   └── td-nl/             # TD-NL skill evolution infrastructure
│       ├── feedback-log.md
│       ├── value-function.md
│       ├── skill-values/   # Per-skill Q^L estimates
│       └── history/        # Spec version archive for rollback
├── scripts/               # Utility scripts (citation, notify, analyzer, install-skills)
├── memory/                # Persistent three-tier memory
│   ├── MEMORY.md          # Always-loaded memory index (written by memory-write)
│   ├── episodes/          # Episodic memories (recent) — YYYY-MM-DD-NNN.md
│   ├── topics/            # Consolidated semantic memories — {topic}-{slug}.md
│   └── procedures/        # Permanent procedural memories — {procedure}-{slug}.md
├── background/            # Research background materials
├── methodology/
│   ├── approach.md        # Authoritative research direction (anchor for writing-* and paper-illustrate)
│   └── ideas/             # Candidate ideas (idea-discover) — YYYY-MM-DD-{slug}.md
├── experiments/
│   ├── {run_id}/          # Per-run configs/results (experiment-run)
│   └── dse/{name}/        # Design-space exploration sweeps (experiment-dse)
├── logs/
│   ├── digest/            # Session logs (session-close) — YYYY-MM-DD.yaml + SUMMARY.md
│   ├── experiments/       # Per-experiment run logs (experiment-run / -monitor) — {exp_id}.yaml
│   └── progress/          # Progress snapshots (progress-capture) — YYYY-MM-DD-{slug}.md
├── paper/                 # Paper sources (written by writing-*, paper-*, proof-write)
│   ├── papers/            # LaTeX sections + references.bib (writing-draft, paper-compile)
│   ├── figures/           # Figure assets (paper-figure, paper-illustrate)
│   │   └── scripts/       # Plot scripts (paper-figure) — {name}.py or .tex
│   ├── proofs/            # Camera-ready proof .tex files (proof-write camera-ready mode)
│   ├── theory/            # Camera-ready theory notes (read by writing-draft)
│   └── reviews/           # Simulated peer reviews (writing-review)
├── outputs/               # Research deliverables
│   ├── short-term/        # Short-term outputs (see also checklists/short-term)
│   ├── mid-term/
│   ├── long-term/
│   ├── paper/             # Compiled paper PDFs (paper-compile) — {name}.pdf
│   ├── visuals/           # Visual identity / pixel art (paper-art) — {name}.svg
│   └── {topic}/           # Topic-scoped proof/theory artifacts
│       ├── proofs/        # Formalized proofs (proof-formalize) — {theorem_name}.tex
│       ├── theory/        # Formalized theory (theory-formalize)
│       ├── counterexamples/   # Counterexample reports (theory-counterexample)
│       └── roadmaps/      # Proof decomposition roadmaps (theory-decompose)
├── resources/             # Reference materials
│   ├── papers/            # Paper reading notes — {paper_id}.md + README.md
│   │   └── searches/      # Literature search results (paper-lit-search) — YYYY-MM-DD-{query}.md
│   └── repos/             # Cloned reference repositories
└── docs/                  # Plans, reports, process docs
    ├── code_reviews/      # Code review reports (code-review) — YYYY-MM-DD-{name}.md
    └── implement_roadmap/ # Implementation roadmaps (code-roadmap) — YYYY-MM-DD-{name}.md
```

## Token Budget

| Operation | Cost |
|-----------|------|
| Session lifecycle (open + close) | ~2-4K |
| G2 inline assessment (per skill firing) | ~100-200 |
| Skill evolution (evolve-suggest) | 2-4K |
| Skill evolution (evolve-apply) | 2-5K |
| Paper analysis | 3-8K |
| Theory formalization | 3-8K |
| Proof refinement | 3-10K/pass |
| Writing (draft/review/polish) | 2-15K |
| Experiment execution (run + monitor) | 2-4K each |
| Idea discovery + novelty verification | 4-8K + 3-6K |
| Planning & progress | 1-5K |
| Memory operations | 1-3K |
