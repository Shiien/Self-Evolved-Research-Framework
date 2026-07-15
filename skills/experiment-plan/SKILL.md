---
name: experiment-plan
description: Design the full experimental spec before any runs — map paper claims to experiments, define independent / dependent variables, pin baselines, schedule ablations, estimate resources, emit one pre-registered experiment contract per launchable experiment, enqueue them in EXPERIMENTS.json, and save to `experiments/{exp_name}/plan.md`. Triggers on "plan experiment", "design experiment", "what experiments should we run", "实验设计", or auto-chains after the `idea` skill's REFINE mode produces a refined proposal. Precondition for `experiment-dse` (hyperparameter sweep over the plan) and `experiment-run` (single-config launch from the plan — which refuses to launch without a contract).
---

# experiment-plan

**Trigger**: User has a refined idea or research question and asks what experiments to run, or auto-invoked after `idea` (refine mode). For hyperparameter sweeps over an already-planned experiment use `experiment-dse`; for launching a single config use `experiment-run`; for analyzing results use `experiment-analyze`.

**Process**:

### 1. Read context

- Refined idea at `methodology/ideas/{slug}.md` (required — if missing, route to `idea` refine mode first)
- Existing experiment configs at `experiments/` (reuse schema conventions; don't invent a new config shape mid-project)
- `resources/papers/` notes for prior baselines + their reported numbers (you will need these for the baselines table)
- `config.yaml` resource budgets (GPU budget, deadline)

If multiple refined ideas exist, ask the user which to plan. Do not combine two ideas into one plan — ablation logic gets tangled fast.

### 2. Extract the testable claims

From the refined idea, list the claims the paper will make in the order they'd appear in a Results section. Each claim becomes one row. Keep claims **falsifiable**:

| # | Claim | How experiment tests it |
|---|---|---|
| C1 | Method M outperforms baseline B on task T | Direct comparison M vs B on T, N seeds |
| C2 | The gain attributes to component X | Ablation: M-without-X vs M |
| C3 | Gain persists at scale (parameter count ≥ S) | Scaling experiment: M and B at 3 sizes |
| C4 | Gain generalizes across domains | M vs B on held-out domains |

Rules:
- Every claim must have exactly one primary experiment. If a claim needs two, it's really two claims — split it.
- Mark claims as **core** (must land for the paper to exist) or **supporting** (strengthens narrative but removable if budget tightens).
- If a claim has no feasible experiment, flag it and refine — unfalsifiable claims shouldn't go into a plan.

### 3. Variable mapping

For each experiment row in the claims table, spec the variables:

- **Independent (what we change)**: method, hyperparameters, data, seed, scale — exactly what is varied, with the specific set of values.
- **Dependent (what we measure)**: primary metric (with its exact definition — "BLEU-4 on WMT14 en-de test set" not just "BLEU"), secondary metrics, and failure indicators (NaN loss rate, OOM frequency).
- **Controlled (held constant)**: hardware, library versions, data preprocessing, eval harness version. Pin these so a future rerun reproduces.
- **Nuisance (expected to vary, averaged out)**: random seed (N ≥ 3 unless compute-bound; N = 5 ideal), data shuffling order, minor non-determinism.

Output a variables table per experiment. Every hyperparameter present in any config must appear in exactly one of the 4 columns — nothing lives outside the table.

### 4. Baselines + fair-comparison checks

For each experiment, pick baselines with a written justification:

| Baseline | Version / config | Why this baseline | Reported number (if any) | Our reproduction target |
|---|---|---|---|---|
| B1 | {exact ref} | {why fair} | {from paper} | {±tolerance we accept} |

Fair-comparison rules:
- Same data split, same eval harness, same metric definition. If any differs, note explicitly why and how you'll reconcile.
- Baselines run under the same controlled variables as the method. No "our method got X tokens; baseline got 0.5X" without correcting.
- If a baseline's reported number can't be reproduced within tolerance, budget time to either reproduce it or document the discrepancy before claiming a win over it.

Include **at least one trivial baseline** (random / majority-class / frozen-pretrained) as a sanity floor.

### 5. Ablation schedule

For claim C2 (and any "the gain attributes to X" claims):

| Ablation | Removes / replaces | Predicts | Budget |
|---|---|---|---|
| A1: no-X | Method M with component X disabled | metric drops to within baseline ± Δ | 1× full-run cost |
| A2: X-only | Only X, rest replaced with baseline defaults | metric improves over baseline by ≥ Δ' | 1× full-run cost |

Ablations come in **pairs** when possible (remove X → should hurt; add X alone → should help). One-directional ablations are weaker evidence.

Order ablations by cost ascending, expected-signal descending. If budget is tight, run the cheap, high-signal ablations first.

### 6. Resource estimate + schedule

Produce a compact table:

| Row | Configs | Seeds | Cost per config | Total GPU-h | Wall-clock (parallel) |
|---|---|---|---|---|---|
| Main comparison | 2 methods × 2 data regimes | 3 | 8 h | 96 | 2 days |
| Ablations | 4 | 3 | 8 h | 96 | 2 days |
| Scaling | 3 sizes × 2 methods | 3 | varies | 180 | 4 days |
| **Total** | | | | **372 GPU-h** | **~8 days** |

- Compare total against `config.yaml` budget + deadline. If over, flag which ablations / seeds to cut first (mark them "trimmable" in the claims table, not "core").
- Reserve 20% headroom for reruns / debugging / surprise OOMs. A plan that assumes zero reruns will blow its budget.

### 7. Save the plan

Write to `experiments/{exp_name}/plan.md`:

```markdown
---
exp_name: "{exp_name}"
idea_ref: "methodology/ideas/{slug}.md"
status: "planned"
created: "YYYY-MM-DD"
deadline: "YYYY-MM-DD"
budget_gpu_h: {N}
seeds: {N}
---

## Claims Table
{from step 2}

## Variable Mapping (per experiment)
{from step 3}

## Baselines
{from step 4}

## Ablation Schedule
{from step 5}

## Resource Estimate
{from step 6}

## Execution Order
1. {trivial baselines — fail fast if anything is broken}
2. {core claim main comparison — fail the paper fast if the headline doesn't land}
3. {ablations — only if main comparison lands}
4. {scaling / generalization — strengthen the narrative}

## Risks
{2-4 items that would force a re-plan — e.g. "baseline B1 not reproducible within ±0.5 BLEU"}

## Contracts
{from step 7b — one per execution-order row}
```

### 7b. Emit one experiment contract per execution-order row

Each experiment that will actually be launched gets a contract, written NOW —
before any result exists (root protocol, `Experiment Protocol`). `experiment-run`
and the harness refuse to launch without one:

```yaml
hypothesis:            # the claim row this experiment tests, falsifiable
change:                # the ONE conceptual factor varied vs the control
controls:              # baseline + everything held fixed
success_metric:        # metric + comparison + reference (decidable, no adjectives)
failure_condition:     # result that counts AGAINST the hypothesis
required_diagnostics:  # artifacts that must exist for any verdict
budget:                # GPU-h / calls / wall-clock
```

Separate dev metrics (free to inspect during development) from held-out
confirmation metrics (checked once, on the final artifact).

### 7c. Enqueue in the ledger

Append one entry per contract to `EXPERIMENTS.json`
(`{"id", "question", "config", "status": "planned", "run": null, "verdict": null}`)
and mirror the ordered list in `RESEARCH_STATE.md § Next recommended
experiments`.

### 8. Handoff

Emit a 3-line summary (exp_name, core-claim count, total GPU-h estimate). Propose the next skill:

**Inputs**: Refined idea at `methodology/ideas/{slug}.md` + `resources/papers/` + `config.yaml`
**Outputs**: `experiments/{exp_name}/plan.md`
**Token**: ~4-10K
**Composition**:
- Plan ready, hyperparameters ranges rather than single values → `experiment-dse` for the sweep
- Plan ready, hyperparameters already committed → `experiment-run` for the first config
- Plan exceeds budget → `decision-analyze` on which experiments to cut
- Plan needs baseline reproductions first → `checklist` (create mode, category=reproducibility) to track each baseline's reproduction targets
- Plan claims need theoretical backing → `theory` (formalize mode) on the core claim before running experiments
- Plan approved → `checklist` (create mode, category=experiment) with one item per execution-order row

## Common pitfalls

- **Claims that aren't falsifiable** — "our method is better" without specifying metric + baseline + margin is untestable. Force step 2 to commit.
- **Conflating "we ran X" with "we proved Y"** — running an experiment isn't the same as the experiment supporting the claim. The "How experiment tests it" column must be pre-committed; no post-hoc narrative-fitting.
- **Ablation asymmetry** — removing a component when adding it alone wasn't also tested gives weak evidence. Pair ablations where possible.
- **Seeds = 1** — single-seed results are noise. Budget N ≥ 3 (ideally 5). If compute prohibits, say so explicitly in the plan and flag the weakened confidence in Risks.
- **Invisible hyperparameters** — a hyperparameter that exists in config but isn't in the variables table hides confounds. Every knob must be accounted for.
- **Baseline cherry-picking** — picking a baseline you know your method beats and omitting a stronger one. List all plausible baselines; exclude by written justification only.
- **No trivial baseline** — without a random / majority-class floor, you can't detect a broken eval harness. Always include one.
- **No reruns budget** — a plan with 0% headroom will overshoot on the first crash. Reserve 20%.
- **Over-planning** — spec-ing 12 experiments before running any is a procrastination pattern. Plan the first 2–3 execution-order rows in detail, sketch the rest, and replan after the first results land.
- **Plan decoupled from Results section order** — if the plan's claims don't map to the paper's section structure, the write-up phase will be painful. Cross-check against the paper outline (`writing` outline mode artifact) before saving if it exists.
