---
name: plan-suggest
description: The SELECT stage of the research loop. Reads RESEARCH_STATE.md (uncertainties + next recommended experiments) and EXPERIMENTS.json first, then the checklist tree for deliverable deadlines, and produces a prioritized list of 3-5 next actions — experiments ranked by uncertainty-resolved-per-cost, deliverables by milestone. Includes a MILESTONE mode (absorbed the former plan-milestone skill): days-to-deadline, phase progress, token budget, on-track/at-risk/behind. Triggers on "what should I do next?", "what's the priority?", "are we on track?", "when is the deadline?", "milestone status".
---

# plan-suggest

**Trigger**: User asks "what should I do next?", "what's the priority?", or
seems unsure about next steps.

**Process**:
1. Read `RESEARCH_STATE.md`: `§ Unresolved uncertainties` (the menu of
   questions worth answering), `§ Active hypotheses` (any stuck at two
   consecutive `inconclusive` verdicts need a narrow/terminate decision
   before anything else), and `§ Next recommended experiments` (already-
   ordered candidates).
2. Read `EXPERIMENTS.json`: planned entries are ready-to-run (contract
   exists); running entries may need monitoring; failed entries may need
   diagnosis/resume before anything new starts.
3. Read `Checklist.md` + relevant L1 checklists and `config.yaml` for
   deliverable deadlines and milestones. Check `IDEA_BACKLOG.md` for any
   parked idea whose revisit condition is now met.
4. Prioritize:
   - a broken baseline or failed/unresumed run outranks everything (the loop
     rule: verify the baseline before new experiments);
   - a hypothesis stuck at two consecutive `inconclusive` verdicts outranks
     fresh exploration — it needs a narrow/terminate decision (root protocol,
     `Hypothesis Closure & Scope Discipline`) before new work starts under
     the same question;
   - experiments: highest uncertainty-resolved-per-cost first — prefer the
     cheapest run that can falsify something (one conceptual factor);
   - deliverables: deadline proximity, then dependency chains;
   - milestone within 7 days overrides ordering.
5. Output 3-5 suggestions, each traceable to a state file:
   ```
   1. [HIGH] {action} — {uncertainty it resolves / milestone impact} (→ exp-NNN | checklists/{path})
   2. [MED]  {action} — {reason}
   3. [LOW]  {action} — {nice-to-have}
   ```
6. No multi-question wizard — direct output. If an experiment is suggested
   that has no contract yet, say so and route to `experiment-plan`.

## Mode: MILESTONE — "are we on track?", "when is the deadline?"

(absorbed from `plan-milestone`) Read `config.yaml` milestones +
`methodology/approach.md` phases; compute days to next milestone, % of phase
tasks completed, token budget remaining; output:
```
Phase {X}: {name} | {start} → {end} ({days_remaining}d remaining)
Progress: ~{pct}% | Token budget: {used}/{allocated}
Risk: {on track / at risk / behind}
```
If behind → run the main SELECT process above with urgency weighting.

**Auto-strategy selection**:
- Near milestone → milestone-critical deliverables first
- Long gap since last session → verify baseline (`python -m harness
  smoke-test`) + review `RESEARCH_STATE.md` first
- Blocked on external → parallel tasks from the ledger/checklists

**Inputs**: RESEARCH_STATE.md, EXPERIMENTS.json, Checklist.md, IDEA_BACKLOG.md, config.yaml
**Outputs**: prioritized action list (inline)
**Token**: ~2-3K
**Composition**: experiment picked → `experiment-plan`/`experiment-run`;
theory task → theory/proof skills; writing task → writing skills.
