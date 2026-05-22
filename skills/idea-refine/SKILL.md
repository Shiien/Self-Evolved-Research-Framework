---
name: idea-refine
description: >-
  Turn a rough research idea (from `idea-discover` or user) into a concrete
  structured proposal: problem statement, proposed approach, key differentiation
  vs SOTA, minimal validation experiment, and resource requirements. Saves to
  `methodology/ideas/{slug}.md` with `status: refined`. Triggers on "refine
  idea", "make this concrete", "sharpen the proposal", "细化想法", or auto-chains
  after `idea-verify` confirms novelty. Closes the gap between ideation
  (`idea-discover -> idea-verify`) and experimental design (`experiment-plan`).
---

# idea-refine

**Trigger**: User wants a rough idea sharpened into a committable proposal — typically after `idea-verify` has confirmed the idea is novel, or when the user says "make this concrete / refine / sharpen / 细化". For generating new ideas from scratch use `idea-discover`; for novelty check against prior work use `idea-verify`; for turning the refined proposal into an experiment spec use `experiment-plan`.

**Process**:

### 1. Read the target idea

- From `methodology/ideas/YYYY-MM-DD-discovery.md` (choose one entry by idea number, or the top-ranked one if unambiguous)
- Or from a user-provided description (inline text / link / file path)
- Pull the matching `idea-verify` report if one exists — its "closest existing work" section is the raw material for step 3 (Differentiation).

If the idea came from `idea-discover`, also read: `methodology/approach.md`, `config.yaml` research keywords, and the top 3 papers referenced in the verify report's "prior work" block. You want to refine against real, not imagined, neighbors.

### 2. Problem anchoring

Answer each in 1–2 sentences. If any answer runs long, the idea is still too fuzzy — push back before continuing:

- **What exactly does this solve?** A single-sentence problem statement. Avoid umbrella phrases like "improve efficiency" — specify *which* efficiency (latency / memory / sample / compute) and *by what axis* (vs baseline X, at scale Y).
- **Who has this problem?** Concrete user / research community / downstream task. If "nobody specifically" — the problem is a solution looking for a problem; either flag that or drop the idea.
- **What is the evaluation metric?** Pick one primary metric and at most two secondaries. Multi-metric "improve all the things" proposals don't survive review.
- **What would success look like?** A concrete number: "reach 85 BLEU on X with ≤60% of Y's parameters". Not "be competitive with SOTA".
- **What would falsify the core claim?** The single experiment whose negative result would kill the idea. If you can't name one, the claim is too soft.

### 3. Frontier alignment

Cite 3–5 **specific** prior papers (not paper categories). For each:

- **Relation**: what the paper does that overlaps with the idea
- **Differentiation**: the one concrete axis on which the refined idea differs (method / setting / claim / data regime)
- **Why the difference matters**: the hypothesis for *why* this axis produces a better outcome

Pull citations from `resources/papers/` if available; otherwise surface the gap by listing the missing citations as a prerequisite for the next step. The differentiation axis should be **factual, not rhetorical** — "we are the first to" is only usable if `idea-verify` supports it; otherwise phrase as "we differ from [paper] by [axis]".

### 4. Implementation orientation

- **Concrete algorithmic steps**: 5–12 numbered steps from input → output. If the algorithm doesn't fit in a dozen steps at this abstraction level, decompose first via `research-explore` or `design-converge`.
- **Data / compute requirements**: dataset name + split + size, GPU-hour estimate (order of magnitude is fine), memory ceiling, any external services.
- **Dependencies**: required libraries / checkpoints / baselines. If any are non-public, note the unblockers now.
- **Minimal validation experiment**: the smallest, fastest experiment whose result would either support or kill the core claim. Target ≤ 24 GPU-hours / ≤ 3 days wall-clock for the first pass. This becomes the primary claim of `experiment-plan`.

### 5. Output the structured proposal

Save to `methodology/ideas/{slug}.md` (slug = short kebab-case phrase derived from the proposal title). If refining an existing discovery entry, the slug should match the original idea title so the history chains:

```markdown
---
title: "{title}"
status: "refined"
refined_from: "{source file or idea number, e.g. 2026-04-21-discovery.md#idea-3}"
verified_by: "{idea-verify report path, or 'pending'}"
date: "YYYY-MM-DD"
primary_metric: "{metric name}"
success_threshold: "{concrete number}"
falsifier: "{one-line experiment that would kill the claim}"
---

## Problem Statement
{precise problem definition — step 2 compressed}

## Proposed Approach
{5-12 numbered algorithmic steps — step 4}

## Key Differentiation
| Prior work | Axis of difference | Why it matters |
|---|---|---|
| {cite} | {axis} | {hypothesis} |
| ...    | ...    | ... |

## Minimal Validation
{smallest experiment that tests the core claim — data, metric, baseline, budget}

## Resource Requirements
- Data: {dataset + split + size}
- Compute: {GPU-hours, memory ceiling}
- Dependencies: {libs / checkpoints / services}
- Risk / unblockers: {if any}

## Open Questions
{2-4 items the user should commit to before `experiment-plan`}
```

### 6. Report back + propose the chain

Emit a 3-line summary (title, primary metric + threshold, minimal-validation cost estimate), then propose the next skill. If any Open Questions are unresolved, flag them as blockers — do not auto-chain into `experiment-plan` with ambiguous success criteria.

**Inputs**: A raw idea (discovery entry, verify report, or user description) + `methodology/approach.md` + `resources/papers/`
**Outputs**: `methodology/ideas/{slug}.md` with `status: refined`
**Token**: ~3-8K
**Composition**:
- Refined proposal + no Open Questions → `experiment-plan` for the experimental spec
- Novelty not yet checked → `idea-verify` before refinement (don't sharpen something that's a re-invention)
- Requires a new theoretical tool → `theory-decompose` or `theory-search`
- Approach needs exploration across multiple method families → `research-explore` first, then re-refine
- Tracks as a methodology commitment → `checklist-create(category=method)` to track the minimal-validation experiment as a deliverable
- User wants to pick among several refined proposals → `decision-analyze`

## Common pitfalls

- **Refining without verifying** — skipping `idea-verify` leads to sharpening a re-invention. Always check for `verified_by:` before writing `status: refined`. If unverified, set `status: "draft"` and link the skipped step.
- **Umbrella problem statements** — "improve robustness" covers ten unrelated problems. Force the primary-metric step to commit to one.
- **Differentiation by rhetoric, not axis** — "our approach is more principled" is not a differentiation axis. Demand a factual, measurable difference.
- **Minimal validation that isn't minimal** — "train for 200 epochs on WMT14" is not minimal. The minimal validation should finish overnight; if it can't, decompose further.
- **Over-specifying the algorithm** — step 4 is a proposal, not an implementation. Pseudocode-level detail is fine; PyTorch-level detail belongs in `experiment-plan` or later.
- **Citations without reading** — listing a paper in "Key Differentiation" without having read it produces bad differentiation claims. If `resources/papers/` lacks the paper, either trigger `paper-read` first or flag the citation as "unverified".
- **Falsifier too weak** — "if BLEU drops" is not a falsifier for a sample-efficiency claim. The falsifier must address the core claim, not a corollary.
- **Refining dead ideas** — if `idea-verify` returned Low novelty (0–1 / 5), do not refine; propose re-entering `idea-discover` with the gap analysis updated. Sunk-cost refinement wastes a rotation.
- **Missing falsifier entirely** — if the author can't name what would kill the claim, the claim is unfalsifiable and should be reformulated before writing `status: refined`.
- **Resource estimates without a ceiling** — "about 100 GPU-hours" with no cap invites scope creep. Always state the budget past which the minimal validation is declared failed.
