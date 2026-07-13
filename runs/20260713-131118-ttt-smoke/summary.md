# Run 20260713-131118-ttt-smoke

- experiment: `ttt_cycle`  seed: 0
- hypothesis: The harness pipeline (self-play -> grading -> G2 -> evolve -> guarded apply -> held-out confirmation) runs end to end deterministically and the scripted engine never forfeits.

- change: None (pipeline validation, not a scientific experiment).
- state: evaluated

## Verdict: **success** (confirmation: True)
- evidence strength: weak (n=1 run)
- budget exceeded: False

### Checks
- success_metric: dev.forfeits=0 <= 0.0 (literal) -> True
- failure_condition: final_spec_valid=True == 0.0 (literal) -> False
- confirmation: confirm.forfeit_rate=0.0 == 0.0 (literal) -> True

### Metrics
```json
{
  "edits_applied": 0,
  "apply_rejected_invalid": 2,
  "final_spec_valid": true,
  "engine_calls": 20,
  "llm_calls": 0,
  "wall_seconds": 0.09,
  "dev.games": 2,
  "dev.forfeits": 0,
  "dev.decisive_wins": 2,
  "dev.draws": 0,
  "dev.total_moves": 14,
  "dev.total_mistakes": 6,
  "dev.clean_games": 0,
  "dev.mistake_rate": 0.42857142857142855,
  "confirm.draw": 0,
  "confirm.win": 0,
  "confirm.loss": 2,
  "confirm.forfeit": 0,
  "confirm.total": 2,
  "confirm.draw_rate": 0.0,
  "confirm.forfeit_rate": 0.0
}
```
