---
name: experiment-monitor
description: Thin wrapper over `python -m harness ext-status` for monitoring external GPU runs. The harness does the deterministic polling (PID liveness incl. --ssh, log tails, OOM/NaN/traceback detection, last metric line); this skill does the judgment — interpret progress, update logs/experiments/*.yaml statuses, decide completed vs failed, and chain to experiment-analyze. Triggers on "how's the experiment?", "check training", "monitor runs", and auto-runs after experiment-run.
---

# experiment-monitor

**Trigger**: Auto after `experiment-run`, or user asks "how's the
experiment?" / "check training".

**Process**:
1. Run the deterministic poll (migrated to the harness — do not re-implement
   ssh/tail/grep by hand):
   ```bash
   python -m harness ext-status --ssh        # active runs; remote liveness + tails
   python -m harness ext-status --ssh --all  # include finished records
   ```
2. **Interpret** each report (this is the judgment the harness doesn't do):
   - alive + metric line progressing → set `status: running`, update
     `last_checked` + `latest_metrics` in `logs/experiments/{exp_id}.yaml`
   - pid DEAD + no error patterns + log shows normal completion → set
     `status: completed`, `ended`, `final_metrics`; collect result files
     from the remote if needed
   - pid DEAD + error patterns (OOM / NaN-loss / traceback / segfault) → set
     `status: failed`, `ended`, `error_summary` (quote the matched lines)
   - `unreachable` host → report it; do NOT guess a status
3. Output the status table (exp_id / machine / status / duration / latest
   metrics).
4. Crashes are failures to diagnose, **not negative evidence** — route to
   the fix, don't write a verdict.
5. Notify via `scripts/notify.py` if `autonomy.auto_proceed` is enabled.

**Inputs**: `harness ext-status` report + `logs/experiments/*.yaml`
**Outputs**: updated yaml records + status table (inline)
**Token**: ~1-2K (the polling itself is free)
**Composition**: completed → `experiment-analyze` (the run is not complete
until evaluated); failed → surface error, suggest fix / re-run.
