---
name: experiment-dse
description: Design-space exploration — systematic hyperparameter sweep over a search space defined by an `experiment-plan`. Picks search strategy (grid / random / Bayesian-inspired sequential), generates a config list as YAML, coordinates batched execution via `experiment-run`, and produces a DSE report at `experiments/dse/{name}/report.md` with best config, sensitivity analysis, and a landscape visualization. Triggers on "DSE", "parameter sweep", "grid search", "explore hyperparameters", "tune", "sweep", "超参搜索". Chains downstream of `experiment-plan` and upstream of `experiment-run` (invoked per-config).
---

# experiment-dse

**Trigger**: User asks to sweep, tune, or explore a hyperparameter space, typically with an existing `experiment-plan` or a set of parameters + ranges. For launching a single committed config use `experiment-run`; for designing the overall experiment spec first use `experiment-plan`; for post-sweep analysis of the winning config's final numbers use `experiment-analyze`.

**Process**:

### 1. Define the search space

- If `experiments/{exp_name}/plan.md` exists, pull the variables table — parameters flagged with ranges (not single values) are the DSE axes.
- Otherwise, ask the user to enumerate each parameter as one of:
  - **Continuous** with range + sampling prior (`lr ∈ [1e-5, 1e-2]`, log-uniform)
  - **Discrete ordinal** (`batch_size ∈ {16, 32, 64, 128}`)
  - **Categorical** (`optimizer ∈ {AdamW, SGD+M, Lion}`)
- **Objective function**: exactly one primary metric to optimize + direction (max / min). Secondaries are reported but do not drive search.
- **Constraints**:
  - Hard budget (max GPU-hours total / max wall-clock)
  - Hard per-config limits (memory ceiling, per-run wall-clock for early-stop)
  - Soft thresholds (minimum acceptable primary metric — below this, don't bother running secondaries)

If the search space is too large for the budget, trim **before** any runs — either reduce ranges, drop parameters to ablation-only, or promote the search to `experiment-plan` if structural changes are needed. Do not start a sweep that can only cover 5% of the space — the result will be misleading.

### 2. Choose search strategy

Pick by space size and prior knowledge, not reflex. Grid search is the default lazy choice and is almost always wrong at scale.

| Strategy | Fits when | Budget needed |
|---|---|---|
| **Grid** | ≤ 50 configs total, no prior on which axes matter | #configs = ∏ axis_sizes |
| **Random** | > 50 configs, high-dim space, unknown sensitivity | 30–100 configs typical |
| **Bayesian-inspired sequential** | Expensive per-config (≥ 4 GPU-h), smooth objective | 20–60 configs, iterative |
| **Latin hypercube / Sobol** | Need uniform coverage with fewer samples than random | 20–50 configs |
| **Successive halving / Hyperband** | Each config has an early-progress signal (loss curve) | High-throughput early eval + long final |

Justify the choice in one sentence in the report header. If Bayesian-inspired, state which surrogate heuristic (EI-like pick of best-margin neighbors, UCB with tunable c, etc.) — no black-box "we used Bayesian" claims.

### 3. Generate config list

Emit a single YAML file at `experiments/dse/{name}/configs.yaml`:

```yaml
dse_name: "{name}"
strategy: "random"          # grid | random | bayes | lhs | hyperband
seed: 42                    # for reproducibility of the sampler itself
plan_ref: "experiments/{exp_name}/plan.md"
objective:
  metric: "val/accuracy"
  direction: "max"
constraints:
  max_total_gpu_h: 200
  max_per_config_gpu_h: 6
  early_stop:
    metric: "val/loss"
    patience_epochs: 3
configs:
  - name: "dse-001"
    params: {lr: 0.001, hidden: 256, dropout: 0.1, optimizer: "AdamW"}
  - name: "dse-002"
    params: {lr: 0.01, hidden: 512, dropout: 0.2, optimizer: "AdamW"}
  # ...
```

- `name` is sequential within this sweep — `{dse_name}-{NNN}`.
- Every `params` dict must be a superset of the plan's controlled variables; only the DSE axes differ.
- For Bayesian-inspired / sequential: emit only the first batch (typically 5–10 configs) and regenerate after results land.

### 4. Execute iteratively

For each batch:

1. Dispatch each config via `experiment-run` (passing `--exp-group {dse_name}` so downstream tooling can group results).
2. Poll via `experiment-monitor` or wait on completion.
3. Collect completed configs into `experiments/dse/{name}/results.csv` with schema: `name, {all params}, {primary metric}, {secondary metrics}, status, wall_clock, gpu_h`.
4. **Early-stop underperformers**: if a config's val metric at 20% of training is ≥ 2σ below current-best-at-same-fraction, kill it and mark `status: early_stopped`. This is the biggest budget-saver; don't skip it unless the metric is too noisy at checkpoint granularity.
5. For sequential strategies: inspect `results.csv`, pick next configs from the surrogate's most-promising region, return to step 3.
6. Stop when any triggers: budget exhausted / no improvement over last B batches (B = 3 default) / user halt.

### 5. Analyze + report

After the sweep concludes, produce `experiments/dse/{name}/report.md`:

```markdown
---
dse_name: "{name}"
plan_ref: "experiments/{exp_name}/plan.md"
strategy: "{strategy}"
configs_completed: N
configs_early_stopped: M
total_gpu_h: {T}
best_config: "{name of winning config}"
best_{metric}: {value}
baseline_{metric}: {value, from plan.md}
---

## Setup
{search space, strategy justification, constraints, any mid-sweep changes}

## Best Configuration
- **Config**: `{name}`
- **Params**: {full param dict}
- **Primary metric**: {value} ({Δ} vs baseline)
- **Secondary metrics**: {table}

## Sensitivity Analysis
For each DSE axis:
- **{param}**: {low / medium / high} sensitivity — {evidence: range of primary metric as param varies with others fixed at best}
- Ranked bar chart: `experiments/dse/{name}/figures/sensitivity.pdf` (via `paper-assets` figure mode)

## Search Landscape
- 2D projections onto the top-2 most sensitive axes (pairplot or heatmap)
- Trajectory (for sequential strategies): primary metric vs config index
- `experiments/dse/{name}/figures/landscape.pdf` (via `paper-assets` figure mode)

## Pareto Frontier (if applicable)
{primary metric vs cost / secondary, with non-dominated configs marked}

## Recommendations
1. **Promote** `{best_config}` to `experiment-run` for full-scale final runs with seeds.
2. **Drop** {list of parameters with negligible sensitivity} from future sweeps.
3. **Narrow** ranges on {list of parameters where optimum is at a boundary — extend the range next sweep}.

## Failed / Early-Stopped Configs
{count + 2-3 representative failure modes — OOM, NaN, diverged}
```

### 6. Handoff

Emit a 4-line summary (dse_name, configs completed, best metric + Δ, recommended next step). Chain to the appropriate next skill.

**Inputs**: `experiments/{exp_name}/plan.md` with parameter ranges + `config.yaml` budget
**Outputs**:
- `experiments/dse/{name}/configs.yaml` (generated configs)
- `experiments/dse/{name}/results.csv` (per-config metrics)
- `experiments/dse/{name}/report.md` (final analysis)
- `experiments/dse/{name}/figures/*.pdf` (sensitivity + landscape plots)

**Token**: ~4-12K (simple grids: 4-6K; Bayesian-sequential multi-batch: 8-12K across iterations)
**Composition**:
- Best config found → `experiment-run` for full-scale final runs (typically at higher seeds, full epochs)
- Sensitivity ranked → update `experiments/{exp_name}/plan.md` variable mapping, drop non-sensitive axes
- Sensitivity plots → `paper-assets` (figure mode) for the landscape / pareto plot; citable in Results as the "tuning protocol" figure
- Pareto frontier matters for claim → `paper-compare` to tabulate against baselines on the pareto
- Optimum at a boundary → re-plan with extended range (re-enter `experiment-plan` or re-sweep with revised configs)
- Sweep exhausted budget without improvement → `decision-analyze` on whether to continue / abandon / re-plan

## Common pitfalls

- **Grid search by reflex** — with N parameters at K values each, grid is K^N. For N ≥ 3, random beats grid at any reasonable sample budget. Use grid only for tiny spaces.
- **Sweeping the wrong parameters** — sweeping learning rate when the real sensitivity is in the data schedule wastes the whole budget. If prior knowledge is thin, run a 20-config random pilot first, inspect sensitivity, then commit the remaining budget to the actually-sensitive axes.
- **No early stopping** — a sweep without per-config early termination burns ≥ 2× the necessary budget. Implement step 4.4 from the start.
- **Fixed seed across sweep** — running all configs with `seed=42` makes the winner look better than average. Once the best config is identified, re-run with N ≥ 3 seeds before declaring it SOTA.
- **Optimum at a boundary** — the best config has `lr = range.max`; you didn't search high enough. Extend the range and re-sweep — do not report the boundary value as the optimum.
- **Comparing non-converged configs** — if some configs didn't finish training, their metric isn't comparable to configs that did. Early-stop is fine (mark them), but report numbers only over completed configs or use a validated proxy (loss at step K for all).
- **Sensitivity computed at a single operating point** — varying one axis with all others fixed *at the best config* can miss interactions. For important axes, compute sensitivity averaged over ≥ 3 settings of the others.
- **Over-long sweeps before checkpointing** — save intermediate `results.csv` after every config. If the process dies after config 50 without a save, the sweep restarts from scratch.
- **No Pareto thinking for multi-objective** — "best accuracy ignoring cost" is rarely the right answer. If cost matters, plot the frontier and let the user pick.
- **Not logging random seed of the sampler** — if the random/Bayesian sampler is itself non-deterministic and unlogged, the sweep isn't reproducible. Log the sampler seed in the report header.
- **Launching configs without quota check** — a 100-config sweep with no total-GPU-h cap can monopolize shared hardware. Honor `constraints.max_total_gpu_h` and check against `config.yaml` before dispatch.
