# Upstream v6 and Codex Runtime Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Subagents are intentionally disabled by this repository's single-model runtime rule. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make local `main` contain all of `upstream/main` while preserving a coherent, tested Codex-native SER v6 runtime.

**Architecture:** Preserve both histories with a merge commit on an isolated branch. Treat upstream's consolidated v6 skills as canonical, make shared manifests runtime-neutral where possible, retain Codex variants only for genuinely runtime-specific behavior, and verify the installed `.agents/skills` surface rather than only the source tree.

**Tech Stack:** Git, Bash installer/tests, Python/pytest, Markdown/YAML skill manifests, SER Python harness.

---

### Task 1: Merge upstream v6 and resolve structural conflicts

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `skills/play-tic-tac-toe/SKILL.md`
- Delete: `skills/idea-refine/SKILL.md`
- Import: all files changed by `upstream/main`

- [ ] **Step 1: Start the merge without committing**

Run:

```bash
git merge --no-ff --no-commit upstream/main
```

Expected: merge stops on the three text conflicts plus the `idea-refine` modify/delete decision.

- [ ] **Step 2: Resolve the upstream-owned protocol files**

Resolve with these exact policies:

```text
CLAUDE.md                            upstream v6 version
skills/play-tic-tac-toe/SKILL.md    upstream strict single-cell-output version
skills/idea-refine/SKILL.md         delete; functionality is consolidated in skills/idea/
```

For `README.md`, start from the upstream version and add back the Codex-native
runtime section from local `main`; change all skill counts/examples in that
section to the consolidated v6 names.

- [ ] **Step 3: Verify conflict resolution and imported ancestry**

Run:

```bash
git diff --check
git diff --name-only --diff-filter=U
git status --short
```

Expected: `git diff --name-only --diff-filter=U` is empty; imported upstream files are staged; no files contain conflict markers.

- [ ] **Step 4: Commit the history-preserving merge**

```bash
git commit -m "merge: integrate upstream SER v6"
```

### Task 2: Add failing Codex v6 integration tests

**Files:**
- Modify: `scripts/test_install_skills.sh`
- Create: `tests/test_codex_protocol.py`

- [ ] **Step 1: Add a failing installer discovery test**

Add this function to `scripts/test_install_skills.sh` and call it with the
other tests:

```bash
test_codex_runtime_ignores_claude_track_only_skills() {
  local source="$TMP_DIR/track-only-source"
  local out="$TMP_DIR/track-only-list.out"

  mkdir -p "$source/track-only"
  printf '%s\n' '---' 'name: track-only' 'description: Claude track only.' '---' >"$source/track-only/SKILL.claude.md"
  cp "$source/track-only/SKILL.claude.md" "$source/track-only/SKILL.codex.md"

  run_install --runtime codex --source "$source" --list >"$out"
  assert_no_grep 'track-only' "$out"
}
```

Extend `test_codex_runtime_installed_surface_is_clean` with:

```bash
for legacy in code-implement code-review code-roadmap idea-refine idea-verify paper-art writing-review; do
  assert_not_exists "$target/$legacy"
done
for consolidated in checklist code idea memory paper-assets proof theory writing; do
  assert_dir "$target/$consolidated"
done
```

- [ ] **Step 2: Add a failing root-protocol test**

Create `tests/test_codex_protocol.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_agents_protocol_exposes_v6_state_owners_and_contract_gate():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for required in (
        ".agents/skills/",
        "RESEARCH_STATE.md",
        "EXPERIMENTS.json",
        "IDEA_BACKLOG.md",
        "runs/",
        "contract",
        "evaluation",
    ):
        assert required in text


def test_agents_protocol_remains_codex_native():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for forbidden in ("/codex:", "mcp__codex__codex", ".claude/skills"):
        assert forbidden not in text
```

- [ ] **Step 3: Run RED tests**

Run:

```bash
bash scripts/test_install_skills.sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_codex_protocol.py
```

Expected: installer test fails because Codex still discovers track-only and/or legacy skills; protocol test fails because old `AGENTS.md` lacks v6 state owners.

- [ ] **Step 4: Commit the regression tests**

```bash
git add scripts/test_install_skills.sh tests/test_codex_protocol.py
git commit -m "test: define Codex SER v6 integration surface"
```

### Task 3: Make Codex discovery follow the consolidated source surface

**Files:**
- Modify: `scripts/install-skills.sh`
- Test: `scripts/test_install_skills.sh`

- [ ] **Step 1: Restrict Codex discovery to usable manifests**

In `discover_skills`, replace the Codex `find` expression with:

```bash
find "$SOURCE_DIR" -type f \
  \( -name 'SKILL.md' -o -name 'SKILL.openai.md' \) \
  -print0 | sort -z
```

Claude discovery continues to include `SKILL.md`, `SKILL.claude.md`, and
`SKILL.codex.md` unchanged.

- [ ] **Step 2: Run the focused discovery test**

Run:

```bash
bash scripts/test_install_skills.sh
```

Expected: track-only discovery now passes; the full-surface test still fails on forbidden runtime coupling or legacy OpenAI variants, proving the next task remains necessary.

- [ ] **Step 3: Commit the discovery fix**

```bash
git add scripts/install-skills.sh
git commit -m "fix: isolate Codex skill discovery from Claude tracks"
```

### Task 4: Remove obsolete Codex variants and neutralize shared manifests

**Files:**
- Delete: `skills/code-implement/SKILL.openai.md`
- Delete: `skills/code-review/SKILL.openai.md`
- Delete: `skills/code-roadmap/SKILL.openai.md`
- Delete: `skills/evolve-apply/SKILL.openai.md`
- Delete: `skills/idea-verify/SKILL.openai.md`
- Delete: `skills/paper-art/SKILL.openai.md`
- Delete: `skills/writing-review/SKILL.openai.md`
- Modify: `skills/code/SKILL.md`
- Modify: `skills/evolve-apply/SKILL.md`
- Modify: `skills/experiment-analyze/SKILL.md`
- Modify: `skills/experiment-plan/SKILL.md`
- Modify: `skills/idea/SKILL.md`
- Modify: `skills/plan-suggest/SKILL.md`
- Modify: `skills/session-close/SKILL.md`

- [ ] **Step 1: Delete pre-consolidation OpenAI variants**

Delete the seven files listed above. Their intent is now owned by the v6
aggregate skills or by a runtime-neutral shared skill.

- [ ] **Step 2: Make protocol references runtime-neutral**

Apply these exact semantic replacements:

```text
CLAUDE.md § Evaluation Guardrails
  -> root protocol § Evaluation Guardrails
CLAUDE.md § Experiment Protocol
  -> root protocol § Experiment Protocol
CLAUDE.md § Hypothesis Closure & Scope Discipline
  -> root protocol § Hypothesis Closure & Scope Discipline
Update CLAUDE.md if behavioral routing changed
  -> update the active root protocol if behavioral routing changed
```

In `skills/code/SKILL.md`, replace the runtime-specific protected-file list
with: “never modify framework instructions, installed skill surfaces, durable
memory, or project configuration unless the task explicitly authorizes it.”

- [ ] **Step 3: Confirm the shared manifests are runtime-neutral**

Run:

```bash
rg -n 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' \
  skills/code/SKILL.md \
  skills/evolve-apply/SKILL.md \
  skills/experiment-analyze/SKILL.md \
  skills/experiment-plan/SKILL.md \
  skills/idea/SKILL.md \
  skills/plan-suggest/SKILL.md \
  skills/session-close/SKILL.md
```

Expected: no matches.

- [ ] **Step 4: Commit the consolidated manifest migration**

```bash
git add skills
git commit -m "refactor: align Codex skills with v6 consolidation"
```

### Task 5: Port the two runtime-specific v6 skills to Codex

**Files:**
- Modify: `skills/experiment-run/SKILL.openai.md`
- Modify: `skills/project-integrate/SKILL.openai.md`

- [ ] **Step 1: Rebase experiment-run on the upstream contract-gated flow**

The OpenAI variant must have the same five-step v6 flow as
`skills/experiment-run/SKILL.md`: contract gate, pre-flight judgment, harness
dispatch, evaluation handoff, and optional notification. Use the Codex helper
path `~/.agents/skills/monitor-gpu-utilization/scripts/gpu_status.sh` when it
exists, otherwise use project-standard monitoring. Replace “user CLAUDE.md”
with “project runtime instructions”. Preserve `python -m harness ext-launch`
and the rule that no valid contract means no launch.

- [ ] **Step 2: Update project-integrate for v6 state ownership**

Keep the existing Codex-native inventory and `.agents/skills` installation,
then add these imported framework paths to its copy/merge inventory:

```text
harness/              deterministic experiment runner
configs/              contract-bearing experiment configs
RESEARCH_STATE.md     scientific state
EXPERIMENTS.json      experiment ledger
IDEA_BACKLOG.md       parked ideas
AGENTS.md             Codex root protocol
```

Require additive merging for user data, install with `--runtime codex`, and
verify `python -m harness setup` plus the installed Codex surface. Do not add
Claude hooks or settings.

- [ ] **Step 3: Verify selected Codex manifests contain no forbidden markers**

Run:

```bash
rg -n 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' \
  skills/experiment-run/SKILL.openai.md \
  skills/project-integrate/SKILL.openai.md
```

Expected: no matches.

- [ ] **Step 4: Commit the v6 runtime-specific ports**

```bash
git add skills/experiment-run/SKILL.openai.md skills/project-integrate/SKILL.openai.md
git commit -m "feat: port contract-gated v6 skills to Codex"
```

### Task 6: Upgrade the Codex root protocol and documentation

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Test: `tests/test_codex_protocol.py`

- [ ] **Step 1: Rewrite AGENTS.md as the Codex v6 protocol**

Include these enforceable sections:

```text
Runtime rules
State ownership
Session lifecycle
Experiment contract and evaluation guardrails
Hypothesis closure
Harness commands
Skill loading and repository boundaries
```

Use `.agents/skills/` and `AGENTS.md` for Codex-specific paths. Keep the v6
state owners and decision taxonomy aligned with upstream `CLAUDE.md`.

- [ ] **Step 2: Reconcile the README Codex section**

Document `--runtime codex`, `.agents/skills/`, `SKILL.openai.md > SKILL.md`,
materialized installs, the consolidated v6 skill families, and the absence of
Claude hooks/cross-model dependencies.

- [ ] **Step 3: Run GREEN protocol and installer tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_codex_protocol.py
bash scripts/test_install_skills.sh
```

Expected: both pass; full Codex install reports zero failed skills and the
legacy inventory assertions pass.

- [ ] **Step 4: Commit protocol migration**

```bash
git add AGENTS.md README.md tests/test_codex_protocol.py scripts/test_install_skills.sh
git commit -m "docs: align Codex runtime with SER v6 protocol"
```

### Task 7: Run full integration verification

**Files:**
- No planned production changes; fix only demonstrated integration failures.

- [ ] **Step 1: Run all repository tests**

```bash
bash scripts/test_install_skills.sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
bash skills/peer-review-sac/tests/test_sac.sh
python -m harness smoke-test
```

Expected: all commands exit zero.

- [ ] **Step 2: Perform a real temporary Codex installation audit**

```bash
bash scripts/install-skills.sh --runtime codex --target /tmp/ser-v6-codex-skills --force
rg -n 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' /tmp/ser-v6-codex-skills
```

Expected: installation exits zero; the marker scan has no matches.

- [ ] **Step 3: Verify history, conflicts, and workspace scope**

```bash
git merge-base --is-ancestor upstream/main HEAD
git diff --check main...HEAD
git diff --name-only --diff-filter=U
git status --short --branch
```

Expected: upstream ancestry succeeds, no whitespace errors, no unmerged files,
and only intentional integration files differ from `main`.

- [ ] **Step 4: Review commits and hand off for local-main integration**

```bash
git log --oneline --decorate main..HEAD
git diff --stat main...HEAD
```

Use `superpowers:finishing-a-development-branch` after fresh verification.
