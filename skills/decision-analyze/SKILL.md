---
name: decision-analyze
description: Structured analysis of a decision — for each option list pros/cons, effort, risk, milestone alignment, and reversibility, then produce a recommendation (user still decides). Includes a CONVERGE mode (absorbed the former design-converge skill) for design/architecture choices — a weighted criteria matrix (novelty/feasibility/alignment/risk) with recommendation, key risk, and first concrete step. Triggers on "should I do X or Y?", "which approach is better?", "weigh these options", "how should we implement X?", or after the idea skill's EXPLORE mode surfaces directions.
---

# decision-analyze

**Trigger**: User weighs options, asks "should I do X or Y?", considers
pivoting, or needs to converge on a design/architecture among concrete
options.

## Mode: ANALYZE (default) — "should I do X or Y?"

1. Identify the decision and options.
2. Per option: pros/cons, effort estimate, risk level, alignment with
   current milestones, reversibility.
3. Present the comparison table + a recommendation with reasoning.
4. Analysis only — the user decides.

## Mode: CONVERGE — "how should we implement X?", design/architecture choices

(absorbed from `design-converge`)
1. Clarify scope: what is being decided (algorithm/architecture/framework)
   and the concrete options (from the `idea` skill's EXPLORE mode or user).
2. Build the weighted criteria matrix — weights from project phase and
   timeline pressure:
   `| Criterion (novelty / feasibility / alignment / risk) | Weight | Option A | B | C |`
3. Recommend: **Recommendation** (top option), **Rationale** (2-3 sentences
   citing scores), **Key risk** + mitigation, **First concrete step**.
4. Record the decision context regardless of acceptance.

**Inputs**: decision context + options
**Outputs**: analysis / criteria matrix (inline)
**Token**: ~2-5K
**Composition**: decision made → record in the owning state file
(`RESEARCH_STATE.md` for scientific direction, `checklist` for deliverable
commitments, `memory` write mode only for durable non-scientific policy);
rejected → refine criteria or back to `idea` (explore mode).
