---
name: experiment-run
description: Launch a training / experiment run — pre-flight GPU check, metadata generation, ssh dispatch to the best available machine, and write logs/experiments/{exp_id}.yaml. Triggers on "run an experiment", "launch training", "test this on GPU", or when the user provides a training script/command to execute.
---

# experiment-run

**Trigger**: User asks to "run an experiment", "launch training", "test this on GPU", or provides a training script to execute.

**Process**:
1. **Pre-flight checks**:
   - Run `bash ~/.agents/skills/monitor-gpu-utilization/scripts/gpu_status.sh` to get GPU availability if that helper is installed; otherwise inspect local and remote GPUs with the project's standard monitoring command
   - Identify best GPU: prefer remote machines, >20 GB free, <10% utilization
   - Verify conda environment exists on target machine
   - Verify the experiment script/command is valid (basic syntax check)
2. **Generate experiment metadata**:
   ```yaml
   exp_id: "exp-{YYYYMMDD}-{NNN}"    # sequential within day
   command: "{full command}"
   machine: "{hostname}"
   gpu: "{CUDA_VISIBLE_DEVICES value}"
   started: "YYYY-MM-DD HH:MM:SS"
   status: "launched"
   working_dir: "{path}"
   log_file: "/tmp/{exp_id}.log"
   config_snapshot: "{key hyperparams or config overrides}"
   ```
3. **Deploy and launch**:
   - For remote: `ssh hsshi@{IP} "cd {working_dir} && CUDA_VISIBLE_DEVICES={gpu} nohup {python} {command} > /tmp/{exp_id}.log 2>&1 &"`
   - For local: `CUDA_VISIBLE_DEVICES={gpu} nohup {command} > /tmp/{exp_id}.log 2>&1 &`
   - Capture PID from launch
4. **Save experiment log**: Write metadata to `logs/experiments/{exp_id}.yaml`
5. **Confirm launch**: Output 3-line status
   ```
   [EXP] {exp_id} launched on {machine} GPU:{gpu}
   Command: {abbreviated command}
   Monitor: experiment-monitor will auto-check, or run manually
   ```
6. **Notify** (if autonomy.auto_proceed enabled): Call `scripts/notify.py` with launch info

**Inputs**: Experiment command/script + optional config overrides
**Outputs**: `logs/experiments/{exp_id}.yaml` + running process on GPU
**Token**: ~2-4K
**Composition**: Launch complete → suggest or auto-trigger `experiment-monitor` after delay

## Experiment Log Format: `logs/experiments/{exp_id}.yaml`

```yaml
exp_id: "exp-20260316-001"
command: "python -m option_exp.entry.run_gymnax +alg=pqn_craftax"
machine: "remote-3"
ip: "172.16.51.3"
gpu: "0"
pid: 12345
working_dir: "~/codeforshare/purejaxql"
log_file: "/tmp/exp-20260316-001.log"
python_path: "/home/hsshi/anaconda3/envs/torch/bin/python"
config_snapshot:
  alg: "pqn_craftax"
  num_seeds: 3
started: "2026-03-16 14:30:00"
ended: null                          # set on completion/failure
status: "launched"                   # launched | running | completed | failed
last_checked: null
latest_metrics: {}
final_metrics: {}
error_summary: null
```

## Autonomy Integration

When `config.yaml § autonomy.auto_proceed` is true:
- `experiment-run` launches without confirmation (after pre-flight passes)
- `experiment-monitor` auto-polls at intervals (composition chain handles scheduling)
- On completion → auto-chains to `experiment-analyze`
- On failure → notifies and pauses for human review (unless `autonomy.auto_retry: true`)

## TD-NL Integration

Tracked via `skills/td-nl/skill-values/experiment-run.md`.
Key metrics for TD assessment: did pre-flight catch issues? did launch succeed? was GPU selection optimal?
