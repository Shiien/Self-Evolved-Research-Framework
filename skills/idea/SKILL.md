---
name: idea
description: Ideation in one mode-based skill — EXPLORE (open-ended: 3-5 research directions with pros/cons/effort, ranked), DISCOVER (gap analysis over papers + methodology → 8-12 scored ideas saved to methodology/ideas/), REFINE (rough idea → committable proposal with problem statement, differentiation table, falsifier, and minimal validation experiment). Absorbs the former research-explore / idea-discover / idea-refine skills — those names now refer to modes here. Novelty checking stays a separate skill (`idea-verify`, codex-track variants). Triggers on "brainstorm ideas", "what are the possible directions?", "find research gaps", "refine this idea", "make this concrete", "细化想法", or "park this idea" / "add to backlog" / "not now" for off-scope ideas.
---

# idea

Novelty checking is the separate `idea-verify` skill (codex-track variants).
Chain: EXPLORE (wide) → DISCOVER (scored) → `idea-verify` → REFINE (sharp) →
`experiment-plan`.

## Mode: EXPLORE — "what are the possible directions?", open-ended

1. Context: `config.yaml` goals/phase, `memory` (retrieve mode),
   `RESEARCH_STATE.md` uncertainties, recent `resources/papers/*.md` Quick
   References.
2. Generate 3-5 directions, each: core idea (1-2 sentences), pros, cons,
   key references from reading history, effort (low/med/high).
3. Rank by novelty × feasibility × alignment; ask the user to pick or refine
   criteria.
→ direction picked: `decision-analyze` (criteria-matrix mode) or DISCOVER.

## Mode: DISCOVER — "brainstorm ideas", "find research gaps"

1. Context as above, plus a **gap analysis**: what the collected papers
   address vs what the current methodology does not; under-explored keyword
   intersections.
2. Generate 8-12 candidates, each:
   core insight · approach · novelty claim · feasibility (H/M/L + why) ·
   alignment (H/M/L + why) · required resources.
3. Rank by `0.4·novelty + 0.3·feasibility + 0.3·alignment`; present top 5.
4. Save to `methodology/ideas/YYYY-MM-DD-discovery.md` (frontmatter: date,
   domain, num_generated, top_idea; sections: Context, Ideas (ranked),
   Verification Results, Selected for Pursuit).
→ top 3 → `idea-verify`.

## Mode: REFINE — "make this concrete", after `idea-verify` confirms novelty

1. **Read the target**: a discovery entry, a verify report (its "closest
   existing work" feeds the differentiation table), or user text. Check
   `verified_by:` — refining an unverified idea gets `status: "draft"`, not
   `"refined"`; a Low-novelty verdict means do NOT refine (back to DISCOVER).
2. **Problem anchoring** — 1-2 sentences each, push back if any runs long:
   what exactly does this solve (which efficiency, vs which baseline)? who
   has this problem? ONE primary metric (+ ≤2 secondary)? success as a
   concrete number, not "competitive with SOTA"? **what would falsify the
   core claim** — the single experiment whose negative result kills it? No
   falsifier = unfalsifiable = reformulate.
3. **Differentiation** — 3-5 *specific* papers: relation, the one concrete
   differing axis (method/setting/claim/data regime), and why that axis
   should matter. Factual, not rhetorical ("more principled" is not an
   axis); unread papers get flagged, not cited.
4. **Implementation orientation** — 5-12 numbered algorithmic steps
   (pseudocode level; PyTorch detail belongs in `experiment-plan`);
   data/compute/dependency requirements with a hard budget ceiling; the
   **minimal validation experiment** (≤24 GPU-h / ≤3 days) that becomes
   `experiment-plan`'s primary claim.
5. Save `methodology/ideas/{slug}.md` — frontmatter: title, status,
   refined_from, verified_by, primary_metric, success_threshold, falsifier;
   sections: Problem Statement, Proposed Approach, Key Differentiation
   (table), Minimal Validation, Resource Requirements, Open Questions.
6. 3-line summary; unresolved Open Questions are blockers — do not
   auto-chain into `experiment-plan` with ambiguous success criteria.

## Scope discipline: parking off-scope ideas

A direction from EXPLORE or a candidate from DISCOVER that doesn't fit the
current `RESEARCH_STATE.md § Current research question` (Level 1) is not
automatically pursued — offer to append it to `IDEA_BACKLOG.md` instead:
`- [ ] {idea} — relates to: {future question} — why not now: {reason} —
revisit when: {condition}`. This keeps scope drift visible instead of silent
(root protocol, `Hypothesis Closure & Scope Discipline`).

**Inputs**: project context, paper notes, discovery entries, verify reports
**Outputs**: inline (EXPLORE) · `methodology/ideas/YYYY-MM-DD-discovery.md`
(DISCOVER) · `methodology/ideas/{slug}.md` (REFINE) · `IDEA_BACKLOG.md`
(off-scope ideas parked)
**Token**: EXPLORE 3-5K · DISCOVER 4-8K · REFINE 3-8K
**Composition**: REFINE with no open questions → `experiment-plan`; needs a
theoretical tool → `theory` (search/decompose modes); choosing among refined
proposals → `decision-analyze`.
