---
name: experiment-run
description: Launch a training / experiment run. The skill owns the judgment — contract gate, GPU selection across the cluster, environment verification — and delegates the mechanical dispatch (nohup/ssh launch, PID capture, record writing with the contract embedded) to `python -m harness ext-launch`, which refuses to launch without a valid contract. For experiments inside the SER repo, delegates to `python -m harness run`. Triggers on "run an experiment", "launch training", "test this on GPU", or when the user provides a training script/command to execute.
---

# experiment-run

**Trigger**: User asks to "run an experiment", "launch training", "test this
on GPU", or provides a training script to execute.

**Process**:

1. **Contract gate (hard requirement)**: locate this run's experiment
   contract — `experiments/{exp_name}/plan.md § Contracts`, the ledger
   entry's config, or user-provided. None exists → DO NOT LAUNCH: draft the
   7 fields with the user (≤10 lines; anything non-trivial → chain
   `experiment-plan`). Save it to a YAML file (or point at the config whose
   `contract:` block holds it) — `ext-launch` validates and embeds it, so
   evaluation criteria are frozen at launch.
   *SER-repo experiments*: skip dispatch entirely — `python -m harness run
   configs/<exp>.yaml`.

2. **Pre-flight judgment**:
   - GPU availability:
     `bash ~/.claude/skills/monitor-gpu-utilization/scripts/gpu_status.sh` —
     prefer remote machines, >20 GB free, <10% util, 1 job per GPU.
   - Verify the target machine's python interpreter actually has the needed
     framework (per-machine paths in user CLAUDE.md — do NOT assume a
     shared env path).
   - Sanity-check the command (module importable, config exists); smoke
     test first when the change is untested (see `run-experiment`
     user-level skill).

3. **Dispatch via the harness** (never hand-roll the ssh/nohup line):
   ```bash
   python -m harness ext-launch \
     --command "<python-path> -m <entry> <overrides>" \
     --machine remote-13 --ip 172.16.51.13 --gpu 0 \
     --workdir "~/codeforshare/<repo>" \
     --contract <contract-or-config>.yaml
   ```
   It validates the contract, launches with `CUDA_VISIBLE_DEVICES`, captures
   the PID, and writes `logs/experiments/{exp_id}.yaml` (status `launched`,
   contract embedded). `--dry-run` to preview.

4. **Confirm + hand off**: report the 3-line launch status; chain
   `experiment-monitor` (which polls via `harness ext-status`). Remember:
   `status: completed` means the process finished — the experiment is
   complete only after `experiment-analyze` judges it against the embedded
   contract.

5. **Notify** if `autonomy.auto_proceed` is enabled (`scripts/notify.py`).

**Inputs**: command + contract + cluster state
**Outputs**: running process + `logs/experiments/{exp_id}.yaml` (written by ext-launch)
**Token**: ~1-3K (dispatch itself is free)
**Composition**: launch → `experiment-monitor` → `experiment-analyze`.
