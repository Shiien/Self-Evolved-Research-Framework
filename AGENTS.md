# AGENTS.md - SER v6 Codex Runtime

You are running Self-Evolved Research (SER) inside Codex. SER is a
behavior-driven research collaboration framework: natural-language intent is
routed to installed skills, scientific claims are tied to experiment evidence,
and durable state is written to explicit project files.

## Runtime rules

- Use Codex-native skills from `.agents/skills/`.
- Treat `AGENTS.md` as the root behavioral protocol.
- Use the active Codex session as the single model for implementation, review,
  writing, judgment, and verification.
- Preserve user work. Never remove untracked files or overwrite populated state
  without explicit authorization.

## First principle

Every research action should advance one evidence transition:

```text
hypothesis -> experiment contract -> execution -> objective evaluation
-> evidence -> next experiment
```

Keep two layers separate:

- **Harness** performs deterministic execution and bookkeeping through
  `harness/`, `runs/`, and `logs/experiments/`.
- **Research loop** selects the question, experiment, interpretation, and next
  action through the state files and SER skills.

Execution success is not scientific success. A launched job, completed process,
or passing training loop becomes evidence only after evaluation against the
pre-registered contract.

## State ownership

Every durable fact has one canonical owner:

| Path | Owns |
|---|---|
| `RESEARCH_STATE.md` | Current research question, active hypotheses, established evidence, unresolved uncertainties, and next recommended experiments |
| `EXPERIMENTS.json` | Experiment ledger: identifiers, questions, configs/contracts, status, run references, and verdicts |
| `runs/<id>/` | Self-contained harness records: resolved config, contract and hash, metadata, metrics, checkpoints, evaluation, failure, and summary |
| `logs/experiments/*.yaml` | External GPU run records with embedded contracts |
| `memory/` | Durable non-scientific context such as preferences, procedures, and environment facts |
| `Checklist.md` and `checklists/` | Deliverable and engineering progress, never experimental evidence |
| `IDEA_BACKLOG.md` | Out-of-scope ideas with a reason and revisit condition |
| `logs/digest/` | Optional narrative session logs, only when requested |

If information could live in two places, use the highest applicable row. In
particular, experimental evidence belongs in `RESEARCH_STATE.md`, not memory or
checklists.

## Session lifecycle

### Session open

At the start of a research session:

1. Read `config.yaml` when present.
2. Read `RESEARCH_STATE.md` and summarize the current question, latest evidence,
   unresolved uncertainty, and next experiment.
3. Read `EXPERIMENTS.json` and report planned, running, completed, and failed
   counts plus the last resolved verdict.
4. Inspect `Checklist.md` only when the request concerns deliverables or project
   execution.
5. Route the user's intent to the matching installed skill before acting.

Keep the opening status concise. Do not ask the user to repeat state already
owned by project files.

### During the session

- Apply `skill-feedback` only when there is a real reward signal: explicit user
  feedback, downstream consumption, or a hard failure.
- Do not treat self-assessment as a reward signal.
- Keep claims linked to run identifiers, metrics, artifacts, or cited sources.
- Park unrelated ideas in `IDEA_BACKLOG.md` instead of silently expanding scope.

### Session close

When the user asks to record, update SER, hand off, or end the session:

1. Update `RESEARCH_STATE.md` with new evidence, changed hypotheses, unresolved
   uncertainty, and the next decisive experiment.
2. Update `EXPERIMENTS.json` for every experiment resolved or status-changed.
3. Write to `memory/` only for durable non-scientific facts.
4. Update checklists only for deliverable progress.
5. Write a digest only when requested.

Do not rely on conversation history as the durable record.

## Experiment protocol

No experiment may launch without a contract written before execution:

```yaml
hypothesis:            # falsifiable statement
change:                # one conceptual factor whenever possible
controls:              # pinned baseline and constants
success_metric:        # decidable comparison and reference
failure_condition:     # evidence against the hypothesis
required_diagnostics:  # artifacts needed for a verdict
budget:                # calls, GPU-hours, or elapsed time
```

Rules:

1. In-repository experiments use `python -m harness run <config>`.
2. External GPU experiments use `experiment-run`, which delegates mechanical
   dispatch and record writing to `python -m harness ext-launch`.
3. Development metrics and held-out confirmation metrics remain separate.
4. Run the cheapest decisive smoke test before a sweep or full-scale run.
5. Confirmation metrics are evaluated once on the final selected artifact.
6. A crash, timeout, NaN, OOM, or wiring error creates a failure record, not a
   scientific verdict against the hypothesis.

## Evaluation guardrails

Prefer deterministic tests, metrics, invariants, artifact checks, and
pre-specified statistical comparisons. An LLM judge is a last resort and must
use criteria written before seeing the result.

Never:

- change success criteria after observing results;
- select only favorable seeds or hide failed runs;
- optimize against held-out confirmation metrics;
- interpret a process crash as negative scientific evidence;
- claim strong support from one noisy run;
- add system complexity without an ablation demonstrating value.

Single-run evidence is marked weak. Claims should report supporting and
contradicting evidence with comparable baselines and exact run references.

## Hypothesis closure

Each active hypothesis closes with exactly one research decision:

| Decision | Meaning |
|---|---|
| `supported` | Accumulated evidence clears the pre-registered support bar |
| `falsified` | Accumulated evidence clears the pre-registered contradiction bar |
| `inconclusive` | Evidence exists but does not clear either bar |
| `terminated` | Work stops because of budget, scope, or supersession before a decisive bar |

A mechanical per-run verdict (`success`, `failure`, or `inconclusive`) is input
to this research decision, not a substitute for it. Two consecutive
`inconclusive` verdicts on the same unchanged hypothesis require narrowing the
claim or marking it `terminated` before another rerun.

Closed hypotheses remain in `RESEARCH_STATE.md` with decision, date, and
evidence reference so failed and superseded directions remain visible.

## Harness commands

```bash
python -m harness setup
python -m harness smoke-test
python -m harness run configs/<experiment>.yaml
python -m harness evaluate <run>
python -m harness resume <run>
python -m harness compare <run> <run> ...
python -m harness status
python -m harness loop step
```

Use `loop step` only when the next ledger entry has a valid contract and the
baseline is verified.

## Skill loading

Installed Codex skills live in `.agents/skills/{skill-name}/SKILL.md`.

- Match the user's intent to the most specific skill description.
- When a skill applies, read its complete `SKILL.md` before acting.
- Resolve referenced files relative to that skill directory.
- Use aggregate v6 skills and their modes instead of resurrecting removed
  pre-consolidation skills.
- If no skill applies, follow the same evidence-first state and safety rules
  directly and produce a concrete next action.

## Repository boundaries

- Keep edits scoped to the active research project.
- Do not rewrite framework instructions unless the user asks to modify SER.
- Do not launch GPU work without satisfying project approval controls.
- Never submit papers, publish artifacts, push branches, or contact external
  parties without the authority required for that action.
- Keep branch synchronization separate from worktree cleanliness when reporting
  Git status.
