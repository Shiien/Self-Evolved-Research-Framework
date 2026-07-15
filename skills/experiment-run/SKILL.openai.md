---
name: experiment-run
description: >-
  Launch a training or experiment run through the SER v6 contract gate. Owns
  GPU selection and environment verification, delegates dispatch and record
  writing to the harness, and requires evaluation before scientific completion.
  Use when the user asks to run an experiment, launch training, test on GPU, or
  provides a training command.
---

# experiment-run

**Runtime**: Codex-native, single model. The active session performs judgment
and uses the repository harness for mechanical launch and bookkeeping.

## Process

1. **Contract gate (hard requirement)**: locate the experiment contract in the
   experiment plan, ledger-linked config, or user-provided input. If none
   exists, do not launch. Draft the seven required fields with the user and
   save them to YAML, or route non-trivial design work to `experiment-plan`.
   For experiments inside the SER repository, use:

   ```bash
   python -m harness run configs/<experiment>.yaml
   ```

2. **Pre-flight judgment**:
   - If installed, inspect cluster availability with
     `bash ~/.agents/skills/monitor-gpu-utilization/scripts/gpu_status.sh`;
     otherwise use the project's standard local and remote monitoring tools.
   - Prefer a suitable remote GPU with more than 20 GB free and less than 10%
     utilization, subject to project policy and user approval requirements.
   - Verify the selected interpreter on the target machine has the required
     framework. Read per-machine paths from project runtime instructions; do
     not assume a shared environment path.
   - Check that the module and config exist, and run the cheapest useful smoke
     test before an untested full launch.

3. **Dispatch through the harness**: never hand-roll the remote background
   launch when the harness supports it.

   ```bash
   python -m harness ext-launch \
     --command "<python-path> -m <entry> <overrides>" \
     --machine remote-13 --ip 172.16.51.13 --gpu 0 \
     --workdir "~/codeforshare/<repo>" \
     --contract <contract-or-config>.yaml
   ```

   Use `--dry-run` to preview. The command validates and embeds the contract,
   applies `CUDA_VISIBLE_DEVICES`, captures the PID, and writes
   `logs/experiments/{exp_id}.yaml`.

4. **Confirm and hand off**: report the concise launch status and route
   monitoring to `experiment-monitor`, which uses `harness ext-status`.
   Process completion is not scientific completion; `experiment-analyze` must
   evaluate the result against the embedded contract.

5. **Notify** if `autonomy.auto_proceed` is enabled and the project provides
   `scripts/notify.py`.

**Inputs**: command, valid contract, and cluster state
**Outputs**: launched process and `logs/experiments/{exp_id}.yaml`
**Composition**: launch -> `experiment-monitor` -> `experiment-analyze`
