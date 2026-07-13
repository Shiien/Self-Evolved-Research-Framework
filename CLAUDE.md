# SER v6.0 — Research Protocol

> Self-Evolved Research: a behavior-driven research collaboration framework.
> Skills trigger via intent detection — no explicit commands needed.

**First principle.** Every piece of research work serves one transition:

```
hypothesis → experiment contract → execution → objective evaluation → evidence → next experiment
```

Two layers, kept separate:
- **Harness** — executes and records experiments (`harness/`, `runs/`,
  `logs/experiments/`). Deterministic, file-based, testable.
- **Loop** — decides what experiment to run next (`RESEARCH_STATE.md`,
  `EXPERIMENTS.json`, this protocol). Judgment lives here, never bookkeeping.

> **Self-Evolving Principle**: the framework improves its own micro-skills
> through use. When a SER skill firing has a real reward signal,
> `skill-feedback` updates that skill's Q^L online (EWMA-with-anchor,
> signal-gated). Audits and spec edits are on-demand via `evolve-suggest` /
> `evolve-apply`.

## Enforcement Priority

**ABSOLUTE RULE — SESSION-OPEN FIRST**: at conversation start, `session-open`
executes BEFORE any other processing, skill evaluation, or response. No
exceptions. SER micro-skills take precedence over external skill systems for
research tasks; external skills (brainstorming, claudeception) keep their
domains but do not override SER intent routing.

## State: single source of truth

Never rely on conversation history as memory. Each fact has exactly one home:

| File | Owns | Written by |
|------|------|-----------|
| `RESEARCH_STATE.md` | Scientific state ONLY: current question, active hypotheses, established evidence, unresolved uncertainties, next recommended experiments | `session-close`, `experiment-analyze`, `harness loop` |
| `EXPERIMENTS.json` | Experiment ledger: id, question, config/contract ref, status, run, verdict | `experiment-plan` (enqueue), `experiment-analyze` / `harness loop` (resolve) |
| `runs/<id>/` | Self-contained harness run records (config, contract+hash, metadata, metrics, checkpoints, eval, failure, summary) | `python -m harness` only |
| `logs/experiments/*.yaml` | External GPU runs (other repos/clusters) — must embed the contract | `experiment-run`, `experiment-monitor` |
| `memory/` | Durable **non-scientific** context: user preferences, procedures, environment facts (see `memory/CLAUDE.md`) | `memory` skill (write/consolidate modes) |
| `Checklist.md` + `checklists/` | Deliverable tracking (paper sections, audits, engineering tasks) — NOT experiment evidence | `checklist` skill (create/update/verify/recount modes) |
| `logs/digest/` | Optional narrative session log — no longer required | `session-close` only if the user asks |

If a fact could live in two places, the leftmost/uppermost row wins. Evidence
goes in `RESEARCH_STATE.md`, never in memory or checklists.

## Session Protocol

### Conversation start → `session-open`

A `SessionStart` hook (`scripts/session_context.sh`) injects deterministic
context: research question, ledger counts, last run + verdict, git state.
`session-open` formats it — do not re-read files the hook already provided:

```
[SER] {project} | Q: {current research question, 1 line}
Ledger: {planned}/{running}/{complete} | last run: {id} → {verdict}
Next: {first planned experiment or "plan one"}
```

Then proceed directly to the user's request without asking questions.

### During session → `skill-feedback`

After a SER skill fires, invoke `skill-feedback` **only when a usable reward
signal exists**: (1) explicit user feedback, (2) downstream consumption, or
(3) hard failure. Self-assessment is not a signal — skip silently. See
`skills/_shared/evolve-cycle.md`. Cost ~80-150 tokens per fire, zero when
gated off.

### Conversation end → `session-close`

Evidence-first close (see `skills/session-close/SKILL.md`):
1. Update `RESEARCH_STATE.md`: new evidence (with run ids + strength stamps),
   changed hypotheses, new uncertainties, next experiments.
2. Update `EXPERIMENTS.json` for anything resolved this session.
3. `memory` (write mode) only for durable non-scientific facts learned.
4. Digest log and skill audit are optional, on user request only.

## Experiment Protocol (harness rules)

1. **Contract before run.** No experiment — harness or external GPU — starts
   without this block, written BEFORE execution:
   ```yaml
   hypothesis:            # falsifiable statement
   change:                # ONE conceptual factor whenever possible
   controls:              # what stays fixed / which baseline
   success_metric:        # metric + comparison + reference, decidable
   failure_condition:     # what would count against the hypothesis
   required_diagnostics:  # artifacts that must exist for a verdict
   budget:                # calls / GPU-hours / minutes
   ```
2. **One canonical path.** In-repo experiments run through
   `python -m harness run <config>` (see `## Harness commands`). External GPU
   experiments run through `experiment-run`, which embeds the contract in
   `logs/experiments/{exp_id}.yaml` and refuses to launch without one.
3. **Execution success is not scientific success.** An experiment is complete
   only when its evaluation has run (`harness evaluate` /
   `experiment-analyze`). "Launched" and "finished training" are not results.
4. **Dev vs confirmation.** Development metrics (`dev.*`) may be looked at
   freely; held-out confirmation metrics (`confirm.*`) are computed once, on
   the final artifact, against the pre-registered criterion.
5. **Cheapest decisive experiment first.** Prefer the smallest run that can
   actually resolve the selected uncertainty; smoke-test before sweeps
   (NUM_SEEDS ≤ 3 unless explicitly requested).

## Evaluation Guardrails (hard rules)

Prefer deterministic graders: tests, metrics, invariants, statistical
comparisons, artifact checks. An LLM judge is a last resort and must judge
against criteria written before seeing the result. Never:

- modify evaluation criteria after observing results (contracts are hashed);
- select favorable seeds or hide failed runs;
- optimize against held-out confirmation metrics;
- treat crashes as negative evidence — a crash is `failure.json`, not a verdict;
- claim support from one noisy run — single runs carry `weak (n=1)` stamps;
- add system complexity without an ablation showing value.

## Research Loop (optional layer)

```
READ_STATE → SELECT_ONE_QUESTION → PROPOSE_ONE_EXPERIMENT → RUN
→ EVALUATE → UPDATE_EVIDENCE → COMMIT_AND_HAND_OFF → REPEAT
```

`python -m harness loop step` executes one iteration mechanically (verify
baseline → run next planned ledger entry → record evidence → commit if
clean). The *judgment* steps — selecting the one falsifiable uncertainty,
designing the contract, deciding what the evidence means — happen in session
via `plan-suggest` → `experiment-plan` → review. Each iteration changes one
conceptual factor, compares against the pinned baseline, records supporting
AND contradicting evidence, and leaves the repo clean and tested.

## Harness commands

```bash
python -m harness setup            # environment check
python -m harness smoke-test       # full deterministic test suite (baseline check)
python -m harness status           # project status: ledger, runs, external runs, checklists
python -m harness ext-status --ssh # poll external GPU runs (liveness, log tails, error patterns)
python -m harness ext-launch ...   # contract-gated external GPU launch (writes the run record)
python -m harness run <config>     # one experiment → runs/<id>/
python -m harness evaluate <run>   # (re-)evaluate against the stored contract
python -m harness resume <run>     # finish a failed/partial run
python -m harness compare <runs>   # metric/verdict table
python -m harness loop step        # dispatch next planned ledger experiment
```

## Intent Router

Grouped by lifecycle stage; priority top → bottom within a group, lifecycle
rows first. Each skill lives in `skills/{name}/SKILL.md` (auto-loaded on fire).

**Session lifecycle**
| Pattern | Skill |
|---|---|
| Conversation start | `session-open` |
| Conversation end | `session-close` |
| SER skill fired + real reward signal | `skill-feedback` |

**READ_STATE / SELECT** — "what's next", "status", "how far along"
| Pattern | Skill |
|---|---|
| What to do next (reads RESEARCH_STATE + ledger first) | `plan-suggest` (milestone mode for "are we on track?") |
| Project status / "where are we" | run `python -m harness status` (deterministic — no skill); narrate briefly |
| Reports completing something ("I did X today") | `checklist` (update mode — routes findings to their owning state files) |
| Weighing options / design convergence | `decision-analyze` (analyze / converge modes) |

**PROPOSE — ideas, theory, design**
| Pattern | Skill |
|---|---|
| Explore directions / brainstorm / refine an idea | `idea` (explore / discover / refine modes) → `idea-verify` for novelty |
| Design experiments / "what should we run" (emits contracts) | `experiment-plan` |
| Hyperparameter sweep / DSE design | `experiment-dse` |
| Theorem/conjecture work (formalize, decompose, stuck, stress-test, generalize) | `theory` (formalize / decompose / search / counterexample / generalize modes) |
| Prove / critique / fix / polish / spot-check a proof | `proof` (write / critique / fix / formalize / verify modes) |

**RUN / MONITOR**
| Pattern | Skill |
|---|---|
| Launch experiment (requires contract) | `experiment-run` |
| Check experiment status | `python -m harness ext-status --ssh` (deterministic poll), then `experiment-monitor` to interpret + update records |

**EVALUATE / UPDATE_EVIDENCE**
| Pattern | Skill |
|---|---|
| Results shared / "what do these mean" (judges vs contract, writes evidence) | `experiment-analyze` |
| Verify paper claims against evidence | `checklist` (verify mode) |

**Literature**
| Pattern | Skill |
|---|---|
| Search literature / arXiv / related work | `paper-lit-search` |
| Discusses/shares a paper | `paper-read`; deep study ("Fey-R") → `paper-read` deep mode → `fey-r` |
| Compare papers / reading-list index | `paper-read` (compare / index modes) |
| Is this idea novel? | `idea-verify` |

**Writing & paper production**
| Pattern | Skill |
|---|---|
| Outline / draft / polish a section | `writing` (outline / draft / polish modes); peer review → `writing-review` |
| Diagrams / plots / decorative art / build PDF ("编译论文") | `paper-assets` (illustrate / figure / art / compile modes; build runs `scripts/compile_paper.sh`) |

**Code**
| Pattern | Skill |
|---|---|
| Branch / roadmap / debug / commit | `code` (branch / roadmap / debug / commit modes) |
| Implement / add feature | `code-implement` (codex-track variants) |
| Review code changes | `code-review` (codex-track variants) → `code` (commit mode) |

**Deliverable tracking & memory**
| Pattern | Skill |
|---|---|
| Add / complete / verify checklist tasks | `checklist` (create/update/verify/recount modes) |
| Remember / recall durable non-scientific context | `memory` (write/retrieve/consolidate/forget modes) |

**Evolution**
| Pattern | Skill |
|---|---|
| Audit skills / propose improvements | `evolve-suggest`; apply approved edit → `evolve-apply` |

No fallback skill: research-adjacent requests with no matching row are handled
directly under this protocol (state table + experiment protocol still apply).

## Skill Evolution (online + on-demand audit)

1. **Online Q-update (`skill-feedback`)**: signal-gated EWMA-with-anchor pull
   on the fired skill's `Q^L`. Hard signals (|delta| ≥ 2) write `[FLAG-HARD]`
   to `skills/td-nl/feedback-log.md`.
2. **On-demand audit (`evolve-suggest`)**: recomputes `V^L`, reads pending
   flags, drafts at most one spec-edit proposal when the signal threshold is
   met.
3. **Apply (`evolve-apply`)**: user-approved edit with version archive +
   rollback (auto-staged if `Q^L` drops ≥1.5 within 5 firings post-edit).

Honesty note: the per-firing math is incremental EWMA, not TD(0). The
deprecated v3 batch pipeline is documented in
`skills/_shared/evolve-cycle.md § Migration notes`. Infrastructure:
`skills/td-nl/`. The evolve *apply* path validates specs before writing
(frontmatter present, no shim placeholders) — see cycle-005 evidence in
`RESEARCH_STATE.md` for why.

## Data Contracts

### `RESEARCH_STATE.md` — exactly five sections
`## Current research question` · `## Active hypotheses` ·
`## Established evidence` (each line: date, exp/run id, SUPPORTS/CONTRADICTS,
criterion detail, strength stamp) · `## Unresolved uncertainties` ·
`## Next recommended experiments`

### `EXPERIMENTS.json` entry
```json
{"id": "exp-NNN", "question": "...", "config": "configs/x.yaml",
 "status": "planned|running|complete|failed", "run": null, "verdict": null}
```

### External run record: `logs/experiments/{exp_id}.yaml`
Legacy fields (exp_id, command, machine, gpu, pid, log_file, config_snapshot)
**plus a `contract:` block** (see Experiment Protocol) — `experiment-run`
refuses to launch without it.

### Paper notes: `resources/papers/{ID}.md`
YAML frontmatter (title, authors, year, venue, relevance, tags, read_date) →
Quick Reference first → Background, Pain Points, Method, Experiments,
Conclusion, Questions, Personal Notes. Reading rule: Quick Reference first;
full document only if needed.

### Checklist items
Leaf `- [ ] {desc}` · Branch `- [3/7] {desc} → checklists/{path}.md` · with
artifact `- [x] {desc} | artifact: outputs/{path}`. Stages: `[ ]`→`[x]`→`[v]`
→`[U]`. Shared vocabulary: `skills/_shared/checklist-engine.md`.

## Project Architecture

```
├── CLAUDE.md              # This protocol
├── RESEARCH_STATE.md      # Scientific state (the loop's memory)
├── EXPERIMENTS.json       # Experiment ledger
├── REFACTOR_PLAN.md       # Harness design + migration record
├── harness/               # Minimal research harness (contract, rundir, cli, loop)
├── configs/               # Experiment configs (each with a contract block)
├── runs/                  # Self-contained run records
├── tests/                 # Harness + regression tests (= baseline check)
├── Checklist.md           # Deliverable tracking root (L0) + checklists/
├── skills/                # 57 SER skills + _shared/ + external/ + td-nl/
├── scripts/               # session_context.sh, evolve_textgrad.py, utilities
├── memory/                # Durable non-scientific context (3-tier)
├── experiments/           # Experiment code (tic_tac_toe/ = legacy + invariant science)
├── logs/                  # experiments/ (external runs) + digest/ (optional)
├── background/ methodology/ resources/ outputs/ docs/
└── config.template.yaml   # Copy to config.yaml and customize
```

## Token Budget

| Operation | Cost |
|-----------|------|
| Session open (hook context is free; banner) | ~0.3K |
| Session close (evidence-first) | ~1-3K |
| skill-feedback (per fire, gated) | ~0.1-0.2K |
| Experiment contract + plan | 2-6K |
| Launch + monitor (external run) | 2-4K each |
| Evaluation / analysis | 3-8K |
| Paper analysis | 3-8K |
| Theory / proof passes | 3-10K |
| Writing | 2-15K |
| evolve-suggest / evolve-apply | 2-4K / 2-5K |
| Memory operations | 1-3K |
