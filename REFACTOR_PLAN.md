# REFACTOR_PLAN — Minimal Research Harness + Optional Loop

Goal: make `hypothesis → contract → execution → evaluation → evidence → next
experiment` reliable, without rewriting working scientific code.

## 1. Repository assessment

**Canonical experiment**: TTT skill evolution (`experiments/tic_tac_toe/`):
play games with the `play-tic-tac-toe` SKILL.md → grade vs minimax → write G2
feedback → `scripts/evolve_textgrad.py` backward pass → apply proposed spec →
re-evaluate. Five historical cycles exist under
`experiments/tic_tac_toe/history/cycle-00{1..5}/`.

**Duplicated execution logic**: `run_cycle.py` contains two ~200-line drivers
(`run_cycle` batch mode, `run_online_evolve_cycle` online mode) that duplicate
pre-flush, snapshotting, evolve-subprocess invocation, proposal
extraction/application, and artifact writing — all against module-global
paths (`SKILL_PATH`, `FEEDBACK_LOG`, `EXP_HISTORY`), which makes runs
non-self-contained and untestable without mutating live repo state.

**Scientific code that must remain invariant** (not edited by this refactor):
- `experiments/tic_tac_toe/game.py`, `minimax.py` — rules + perfect-play oracle
- `experiments/tic_tac_toe/arena.py` — agent protocol, game runner, `grade_game`
- `experiments/tic_tac_toe/g2_writer.py` — G2 entry format + reward mapping
- `skills/td-nl/textgrad_backend/` — TD layer, backward pass, proposal writer

**Smallest vertical slice**: one consolidated cycle runner (both modes) inside
the harness, artifacts in a self-contained `runs/<id>/`, sandboxed skill/log
state, deterministic scripted engine + `--no-engine` evolve for smoke testing.

**Baseline defect found during assessment**: `skills/play-tic-tac-toe/SKILL.md`
is corrupted — during cycle-005 the apply step wrote raw `<<EVOLVE NOTE>>`
shim/error text as the spec (claude CLI was erroring; the deterministic shim's
placeholder "diff" was applied verbatim). This caused cycle-005's 8/10 forfeit
rate. Remediation (documented state change, not a code change):
- restore `SKILL.md` from the identical archived good versions
  (`experiments/tic_tac_toe/history/v1-initial/SKILL.md` ==
  `skills/td-nl/history/play-tic-tac-toe-v2.md`); archive the corrupted spec
  to `skills/td-nl/history/` first;
- the harness apply step validates a proposed spec (YAML frontmatter present,
  no `<<EVOLVE NOTE` markers) and refuses to apply invalid ones. This is a
  deliberate, tested behavioral difference vs the legacy driver.

## 2. Design

Two layers, kept separate:

- **Harness** (`harness/`): executes and records one experiment.
  `resolved config → setup → execute → evaluate → artifacts in runs/<id>/`.
- **Loop** (`harness/loop.py`): decides/dispatches the next planned experiment
  from `EXPERIMENTS.json`; persists evidence in `RESEARCH_STATE.md`. Optional —
  the harness is fully usable without it.

```
harness/
  contract.py      # experiment contract: parse, validate, hash, criteria eval
  rundir.py        # self-contained run directory (config, meta, status,
                   # metrics.jsonl, logs/, checkpoints/, eval/, failure.json,
                   # summary.md)
  experiments/
    ttt_cycle.py   # migrated TTT experiment: execute() + evaluate()
  cli.py           # setup | smoke-test | run | evaluate | resume | compare | loop
  loop.py          # READ_STATE → SELECT → RUN → EVALUATE → UPDATE_EVIDENCE → COMMIT
configs/           # config + contract per experiment
runs/              # one self-contained directory per run
tests/             # harness unit tests + deterministic end-to-end smoke
RESEARCH_STATE.md  # question, hypotheses, evidence, uncertainties, next exps
EXPERIMENTS.json   # experiment ledger (planned/running/complete + verdicts)
```

Experiment interface is two explicit functions per experiment module — no
registry framework:

```python
def execute(params: dict, run: RunDir) -> dict      # raw results
def evaluate(params: dict, run: RunDir, contract: Contract) -> dict
```

Contract (required before any run):

```yaml
contract:
  hypothesis: ...
  change: ...
  controls: ...
  success_metric:    {metric: dev.mistake_rate, op: "<=", value: 0.05}
  failure_condition: {metric: dev.forfeits,     op: ">=", value: 2}
  confirmation:      {metric: confirm.forfeit_rate, op: "==", value: 0.0}  # held-out, optional
  required_diagnostics: [games.jsonl, engine-calls.jsonl]
  budget: {max_llm_calls: 0, max_minutes: 5}
```

Evaluation rules enforced by the harness:
- contract is hashed at run creation; `evaluate` refuses if the run's contract
  was edited afterwards;
- `dev.*` metrics (self-play grading) are separated from `confirm.*` metrics
  (held-out eval vs minimax with the final spec);
- a crash produces `failure.json` and **no verdict** (never negative evidence);
- single-run verdicts are stamped `evidence_strength: weak (n=1)`;
- verdicts are deterministic comparisons; no LLM judge anywhere in evaluation.

## 3. Changes to existing code (exhaustive)

1. `scripts/evolve_textgrad.py`: add optional `--feedback-log`,
   `--skills-root`, `--skill-values-dir`, `--value-function` path flags
   (defaults = current hard-coded repo paths; behavior unchanged when omitted).
   Needed so a run can operate on its own sandboxed state.
2. `skills/play-tic-tac-toe/SKILL.md`: restore from archived good version
   (see baseline defect above).
3. `experiments/tic_tac_toe/run_cycle.py`: **frozen, not edited** — kept as
   the legacy driver for reproducing cycles 001–005. Its pure helpers
   (`summarize`, `summarize_selfplay`, `extract_last_proposal`,
   `extract_proposal_spec`, `games_to_jsonl`) are imported by the harness so
   parsing/summarizing semantics stay single-sourced. Delete after the harness
   has produced equivalent real-engine cycles.

Everything else is additive.

## 4. Verification strategy

- **Invariance by construction**: the harness imports `arena.play_one_game`,
  `arena.grade_game`, `g2_writer.write_*`, and the evolve CLI unchanged, so
  game semantics, grading, G2 format, and TD math are byte-identical to legacy.
- **Regression test against historical artifacts**: re-grade the recorded
  games in `history/cycle-003/games-selfplay.jsonl` and assert `grade_game`
  reproduces the stored mistake counts.
- **Existing pure tests** (`test_game.py`, `textgrad_backend/test_smoke.py`)
  run in the smoke suite untouched.
- **Deterministic end-to-end**: scripted first-legal-move engine +
  `--no-engine` evolve, sandboxed state, asserts the full run-directory
  contract (config, meta, status, metrics, checkpoints, eval, summary).

## 5. Steps

1. Write this plan. ✅
2. Restore corrupted SKILL.md baseline (archive corrupt copy). ✅
3. Add path flags to `evolve_textgrad.py`. ✅
4. Implement `harness/` (contract, rundir, ttt_cycle, cli) + configs + tests. ✅
5. Run smoke suite; fix until green. ✅ (37 tests: 24 harness + 6 legacy game
   + 7 textgrad backend)
6. Add `harness/loop.py` + seed `RESEARCH_STATE.md` / `EXPERIMENTS.json` from
   the real cycle-001..005 evidence; validate one loop step on the
   deterministic smoke experiment. ✅ (exp-000 → success, run
   `20260713-131118-ttt-smoke`)
7. Hand off: real-engine experiments (exp-001 baseline eval, exp-002
   online-evolve) left as `planned` in the ledger — they cost LLM calls and
   should be launched deliberately with `python -m harness loop step`.

## 6. Phase 2 — meta-level framework refactor (CLAUDE.md v6)

The behavioral framework itself had the defects the first principle warns
about, so the same harness/loop discipline is applied to the protocol layer:

**Diagnosis (v5):**
- **State fragmentation**: five stores (`logs/digest/`, `memory/` 3-tier,
  `Checklist.md` tree, `td-nl/` values, `config.yaml`) — none of them held the
  *scientific* state (hypotheses, evidence, uncertainties). Session-close
  wrote conversation summaries, i.e. it relied on conversation history as
  memory.
- **No experiment contract at the behavioral level**: `experiment-run`
  terminated at status "launched" — execution success was treated as
  completion; evaluation (`experiment-analyze`) was a separate, optional
  intent with no pre-registered criteria.
- **Bookkeeping done by the LLM**: session-open "silently read 5 files" every
  conversation — expensive and unreliable, where a deterministic hook can
  inject the same context for free.
- **Flat 42-row intent router** with no notion of the research lifecycle.

**Changes (v6):**
1. `CLAUDE.md` rewritten around `hypothesis → contract → execution →
   evaluation → evidence → next`: state table with one owner per file,
   session protocol reads/writes `RESEARCH_STATE.md` + `EXPERIMENTS.json`,
   experiment protocol requires a contract before any run (harness runs AND
   external GPU runs), evaluation guardrails are hard rules, router grouped
   by loop stage. `logs/digest/` demoted to optional.
2. `.claude/settings.json` (checked in): `SessionStart` hook runs
   `scripts/session_context.sh` — deterministic session context (research
   question, ledger counts, last run verdict, git state) injected at zero
   model cost; `session-open` formats instead of re-reading.
3. Lifecycle skills rescoped: `session-open`, `session-close` (evidence-first
   close), `experiment-plan` (emits contracts), `experiment-run` (refuses to
   launch without a contract; launch ≠ complete), `experiment-analyze`
   (= evaluation stage, judges against the pre-registered contract, updates
   `RESEARCH_STATE.md`/ledger), `plan-suggest` (reads research state before
   checklists).
4. Kept: the 57-skill inventory, signal-gated `skill-feedback` Q^L updates,
   memory tiers (rescoped to durable *non-scientific* context), checklist
   engine (rescoped to deliverable tracking, e.g. paper audits).

## 7. Phase 3 — skill consolidation (57 → ~20, incremental)

Principle: **deterministic bookkeeping becomes harness code; judgment stays in
skills; families of near-identical skills merge into one mode-based skill.**
Merged skills keep the old names as documented modes (e.g. `memory-write` is
now "the write mode of `memory`"), so stale cross-references in other skills
still resolve; those references get cleaned opportunistically as each skill is
next touched. Old specs are recoverable from git history.

| Disposition | Skills | Where it goes |
|---|---|---|
| **Migrate to harness (tranche 1)** ✅ | `status-report`, `checklist-status` (read/report path) | `python -m harness status` — deterministic aggregation of ledger, runs, external run records, checklist counts |
| **Merge (tranche 1)** ✅ | `checklist-create/update/verify/status` → `checklist`; `memory-write/retrieve/consolidate/forget` → `memory` | one mode-based SKILL.md each |
| **Retire (tranche 1)** ✅ | `general-research` (fallback = default behavior) | router fallback row removed |
| **Merge (tranche 2)** ✅ | `theory-*` (5) → `theory`; `proof-*` (5) → `proof`; `writing-outline/draft/polish` → `writing`; `idea-discover/refine` + `research-explore` → `idea`; `plan-milestone` → `plan-suggest` (milestone mode); `design-converge` → `decision-analyze` (converge mode); `progress-capture` → `checklist` update mode; `paper-compare`/`paper-index` → `paper-read` modes. (`writing-review` and `idea-verify` stay standalone — they ship codex-track variants; fold them in tranche 3 together with the code-family decision.) | mode-based skills |
| **Migrate to harness (tranche 2)** ✅ | `experiment-monitor` polling core (PID liveness incl. --ssh, log tails, OOM/NaN/traceback patterns, last metric line) | `harness ext-status`; skill rewritten as a thin judgment wrapper (interprets reports, owns yaml status writes) |
| **Migrate to harness (tranche 3)** | `experiment-run` dispatch mechanics (ssh/tmux launch, record writing); `experiment-dse` config-list generation; `paper-compile` build pipeline | harness subcommands / scripts; skills keep only the judgment (contract gate, GPU choice rationale, search-strategy choice) |
| **Merge or defer to superpowers (tranche 3)** | `code-branch/roadmap/implement/review/debug/commit` (overlap with superpowers TDD/debugging/worktrees; codex-track variants complicate — decide with user) | TBD |
| **Keep as skills** | `session-open`, `session-close`, `skill-feedback`, `evolve-suggest`, `evolve-apply`, `plan-suggest`, `decision-analyze`, `experiment-plan`, `experiment-run` (thin), `experiment-analyze`, `idea`, `theory`, `proof`, `writing`, `paper-read`, `paper-lit-search`, `paper-illustrate`, `paper-figure`, `paper-art`, `checklist`, `memory`, `project-integrate` | judgment-heavy |

Tranche 1 executed 2026-07-13: 57 → 49 skills
(−4 checklist +1, −4 memory +1, −`status-report`, −`general-research`).

Tranche 2 executed 2026-07-13: 49 → 32 skills
(−5 theory +1, −5 proof +1, −3 writing +1, −3 idea +1, −`plan-milestone`,
−`design-converge`, −`progress-capture`, −`paper-compare`, −`paper-index`;
`experiment-monitor` polling → `harness ext-status`).

Tranche 3 executed 2026-07-13: 33 → 27 skills (the tranche-2 tally of 32 had
missed `skill-feedback`; corrected here):
- `code-branch/roadmap/debug/commit` → `code` (BRANCH/ROADMAP/DEBUG/COMMIT
  modes; the roadmap file format is preserved verbatim — it is the execution
  contract `code-implement` consumes).
- `paper-illustrate/figure/art/compile` → `paper-assets`
  (ILLUSTRATE/FIGURE/ART/COMPILE modes); the deterministic LaTeX build
  (main resolution, integrity pre-checks, pdflatex×3 + bibtex/biber, issue
  summary) migrated to `scripts/compile_paper.sh`.
- `experiment-run` dispatch mechanics → `python -m harness ext-launch`:
  validates the 7-field contract BEFORE any side effect (no contract, no
  launch), builds the nohup/ssh launch line, captures the PID, writes
  `logs/experiments/{exp_id}.yaml` with the contract embedded. The skill
  keeps only judgment (GPU selection, env verification).
- Settled principle: **skills shipping codex-track variants stay standalone**
  (`code-implement`, `code-review`, `writing-review`, `idea-verify`) —
  merging them would either break the `--codex-track` installer mechanism or
  force duplicating each merged body across two variant files. Folding them
  further would require dropping the codex track or a variant-composition
  installer feature; user decision if the count should go below 27.

Final inventory (27): session-open, session-close, paper-lit-search,
paper-read, paper-assets, writing, writing-review, theory, proof, idea,
idea-verify, plan-suggest, decision-analyze, experiment-plan, experiment-dse,
experiment-run, experiment-monitor, experiment-analyze, code, code-implement,
code-review, checklist, memory, skill-feedback, evolve-suggest, evolve-apply,
project-integrate.

## 8. Phase 4 — merge `research-closure-harness` concepts (2026-07-14)

An external candidate package (`ideas/research-closure-harness/`, a
standalone claim-to-evidence-to-decision governance layer with its own CLI —
`tools/research_closure.py` — and JSON state store, `.research/state.json`)
was evaluated for merging in. Its closure engine (contract → run → evaluate
→ evidence) duplicates what `harness/` already does more rigorously
(hash-locked contracts, deterministic verdicts, dev/confirm metric split);
adopting its parallel JSON state store would have violated `CLAUDE.md §
State`'s single-source-of-truth rule. Its global installer (patches
`~/.claude/CLAUDE.md` / `settings.json` machine-wide, affecting every other
project) was out of scope entirely and was not run.

**Extracted (conceptual only, no new mechanical enforcement):**
- A four-outcome hypothesis-closure decision taxonomy
  (`supported`/`falsified`/`inconclusive`/`terminated`). The `terminated`
  case (abandon before a bar is reached — budget exhausted, scope cut,
  superseded) didn't exist in v6; added as a judgment-level annotation on
  `RESEARCH_STATE.md § Active hypotheses`, distinct from the harness's
  per-run mechanical verdict (`success`/`failure`/`inconclusive`).
- Anti-pattern rule: two consecutive `inconclusive` verdicts on the same
  hypothesis force a narrow-or-terminate decision at the next opportunity,
  instead of silently rerunning variations of an untightened contract
  (`CLAUDE.md § Hypothesis Closure & Scope Discipline`). Wired into
  `experiment-analyze` and `plan-suggest`.
- Claim-stability-level vocabulary (agenda / question / hypothesis /
  experiment) mapped onto existing files — documentation only, no new file.
  This repo runs multiple parallel experiments across a 5-machine GPU
  cluster, so strict WIP=1 nesting was explicitly rejected (user decision) —
  only Level 3 (one contract, one run) stays mechanically gated.
- `IDEA_BACKLOG.md`: a genuinely new, previously-missing capability — a flat
  file for parking off-scope ideas with a revisit condition, so scope drift
  stays visible instead of silent. Wired into `idea` (explore/discover
  modes), `plan-suggest`, and `session-close`.

**Not adopted:** the parallel `.research/state.json` + CLI, the global
installer, the keyword-triggered `PreToolUse` blocking hook, templates
(`sprint_plan.md`, `weekly_review.md`, etc. — SER's existing
`RESEARCH_STATE.md`/`Checklist.md`/`checklist` skill already cover that
ground), and strict WIP=1 enforcement at the experiment level.
