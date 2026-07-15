---
name: experiment-analyze
description: The EVALUATE stage of the research loop. Judges experiment results against the pre-registered contract (never against post-hoc criteria), classifies the outcome as supporting/contradicting/inconclusive evidence with a strength stamp, and persists the verdict to RESEARCH_STATE.md and EXPERIMENTS.json. Triggers when the user shares training logs, metrics, or asks "what do these results mean?", "are these results good?", or auto-chains after experiment-monitor reports completion.
---

# experiment-analyze

**Trigger**: User shares experiment results, training logs, or metrics; asks
"what do these results mean?"; or an external run reaches `completed`.

**Principle**: an experiment is complete only when this stage has run.
Judgment happens against criteria written BEFORE the result existed.

**Process**:
1. **Retrieve the contract** for this run: `runs/<id>/contract.yaml` (harness
   runs — prefer `python -m harness evaluate <run>`, which is deterministic
   and tamper-checked), `logs/experiments/{exp_id}.yaml § contract`, or
   `experiments/{exp_name}/plan.md § Contracts`. If no contract exists, say
   so explicitly: the analysis is then EXPLORATORY and may generate
   hypotheses but not evidence — offer to write a contract for a
   confirmatory rerun.
2. **Parse the results** (tables, metrics, W&B, logs). Check
   `required_diagnostics` exist; missing diagnostics → inconclusive.
3. **Judge deterministically** against `success_metric` /
   `failure_condition`: prefer computed comparisons (mean ± std over seeds,
   tests, invariants) over prose judgment. Keep `dev.*` and `confirm.*`
   metrics separate; a claim confirmed only on dev metrics is not confirmed.
4. **Guardrails** (from the root protocol's `Evaluation Guardrails` section):
   - a crash/NaN/OOM is a failure record, NOT negative evidence — route to
     `code` (debug mode) / resume instead of a verdict;
   - single noisy runs get `strength: weak (n=1)` — never "shows" or
     "proves";
   - if the observed result makes a different criterion look more
     appropriate, record the pre-registered verdict FIRST, then propose the
     new criterion as a new experiment.
5. **Persist the evidence** (this step is not optional):
   - `RESEARCH_STATE.md § Established evidence`: `[date] {exp/run id}:
     SUPPORTS/CONTRADICTS — {question} | {criterion detail} | strength: {stamp}`;
     inconclusive outcomes go to `§ Unresolved uncertainties` with what would
     sharpen them.
   - `EXPERIMENTS.json`: set `status`, `run`, `verdict` on the ledger entry.
   - If this is the hypothesis's **second consecutive `inconclusive`**
     verdict, don't queue a third unchanged rerun: propose a narrower
     hypothesis (tighter contract) or mark it `terminated`. When evidence
     clears the bar either way, annotate `§ Active hypotheses` with
     `[decision: supported|falsified, date, evidence ref]` (root protocol,
     `Hypothesis Closure & Scope Discipline`) — don't leave a decided
     hypothesis looking still-open.
6. **Propose the next experiment**: the cheapest run that resolves the
   sharpest remaining uncertainty, one conceptual factor changed. Append to
   `§ Next recommended experiments`.

**Inputs**: results + the pre-registered contract
**Outputs**: verdict + updated `RESEARCH_STATE.md` / `EXPERIMENTS.json`; analysis inline
**Token**: ~3-8K
**Composition**: supported core claim → `writing` (draft mode) + `checklist`
(update mode); contradicted → `decision-analyze`; crashed → `code` (debug mode);
inconclusive → `experiment-plan` for a sharper contract.
