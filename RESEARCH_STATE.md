# Research State

> Persistent research memory. Updated by `python -m harness loop step` and by
> hand. Never rely on conversation history — this file, `EXPERIMENTS.json`,
> and `runs/` are the memory.

## Current research question

Does TextGrad TD-NL online evolution (per-game G2 → TD backward pass → spec
apply) improve the `play-tic-tac-toe` SKILL.md beyond the hand-written v1
baseline — fewer minimax-graded mistakes and no forfeit regression on held-out
evaluation vs perfect play?

## Active hypotheses

- H1: Online evolution with a **real** LLM engine reduces held-out
  mistakes/forfeits relative to the frozen v1 spec (untested — every
  historical cycle either applied no edit or applied corrupted shim text).
- H2: Spec application without validity checking corrupts specs when the
  engine errors (SUPPORTED — see evidence from cycle-005; the harness now
  guards applies).

## Established evidence

- [2026-07-13] Legacy cycle-001 (vs minimax, haiku, n=2/side): v1 spec drew
  every game before AND after one batch evolve pass (draw_rate 1.0, 0
  forfeits). Strength: weak (n=2 games/side, single cycle).
- [2026-07-13] Legacy cycles 002–003 (self-play, haiku, 10 games each):
  mistake_rate 0.0, but 1–2 forfeits per cycle from output-format failures;
  cycle-003 online evolution applied 0 edits (td strength never reached
  'hard' on drawing games). Strength: weak.
- [2026-07-13] Legacy cycle-005 (online-evolve, sonnet, 10 games): the claude
  CLI was erroring, the deterministic shim's placeholder "diff" was applied
  verbatim 3 times, corrupting SKILL.md into `<<EVOLVE NOTE>>` text →
  8/10 forfeits. SUPPORTS H2. The corrupted spec was archived and restored to
  v1 during the 2026-07-13 harness refactor; the harness apply step now
  rejects invalid specs (regression-tested).
- [2026-07-13] exp-000 (run 20260713-131118-ttt-smoke): SUPPORTS — Does the migrated harness pipeline reproduce the legacy cycle semantics deterministically (scripted engine, shim evolve, guarded apply)? | dev.forfeits=0 <= 0.0 (literal) -> True | strength: weak (n=1 run)

## Unresolved uncertainties

- Whether evolution helps at all (H1): no cycle has yet shown a real-engine
  edit improving held-out performance.
- Legacy cycle-004 crashed mid-run (no eval.json); cause undiagnosed.
- Eval noise: n≤10 games per condition — verdicts at this n are weak evidence
  by construction.
- Whether haiku's forfeit rate (output-format failures) is spec-fixable or an
  engine floor.

## Next recommended experiments

1. exp-001 (`configs/ttt_baseline_eval.yaml`): re-measure the restored v1
   baseline vs minimax (3/side, haiku, no evolution) → reference confirm.*
   numbers.
2. exp-002 (`configs/ttt_online_evolve.yaml`): ONE factor changed vs exp-001 —
   online evolution enabled (real engine, guarded apply). After exp-001,
   point its success_metric at `baseline_run: <exp-001 run id>`.
3. If exp-002 shows no applied edits again: lower the TD 'hard' threshold OR
   enrich G2 evidence with per-move minimax traces — one factor at a time.
