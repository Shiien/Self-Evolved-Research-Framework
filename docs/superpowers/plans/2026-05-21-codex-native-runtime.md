# Codex-Native Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Codex-native single-model runtime path to SER while preserving the existing Claude Code runtime and its `--codex-track claude|codex` behavior.

**Architecture:** The installer gains a `--runtime claude|codex` axis. Claude runtime keeps `.claude/skills` and current Track A/Track B variant selection; Codex runtime installs to `.agents/skills`, selects `SKILL.openai.md > SKILL.md`, and audits the installed skill surface for Claude Code runtime coupling.

**Tech Stack:** Bash installer and shell tests; Markdown runtime instructions and skill variants.

---

## File Structure

- Create `AGENTS.md`: Codex-native root instruction file adapted from `CLAUDE.md`.
- Modify `scripts/install-skills.sh`: add runtime parsing, target defaults, variant selection, and Codex audit.
- Create `scripts/test_install_skills.sh`: shell regression tests for Claude and Codex install behavior.
- Create `skills/code-implement/SKILL.openai.md`: Codex-native single-model implementation skill.
- Create `skills/code-review/SKILL.openai.md`: Codex-native single-model review skill.
- Create `skills/writing-review/SKILL.openai.md`: Codex-native single-model writing review skill.
- Create `skills/idea-verify/SKILL.openai.md`: Codex-native single-model novelty verification skill.
- Create `skills/project-integrate/SKILL.openai.md`: Codex-native integration skill using `AGENTS.md` and `.agents`.
- Modify `README.md`, `README.zh-CN.md`, `scripts/README.md`, `scripts/CLAUDE.md`: document dual runtime installation.
- Keep existing `CLAUDE.md`, `SKILL.claude.md`, and `SKILL.codex.md` semantics unchanged.

---

### Task 1: Installer Regression Test Scaffold

**Files:**
- Create: `scripts/test_install_skills.sh`

- [ ] **Step 1: Write failing shell tests**

Create `scripts/test_install_skills.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="${REPO_ROOT}/scripts/install-skills.sh"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

assert_file() {
  [ -f "$1" ] || fail "missing file: $1"
}

assert_dir() {
  [ -d "$1" ] || fail "missing dir: $1"
}

assert_not_exists() {
  [ ! -e "$1" ] || fail "unexpected path exists: $1"
}

assert_grep() {
  local pattern="$1" file="$2"
  grep -Eq "$pattern" "$file" || fail "pattern not found in $file: $pattern"
}

assert_no_grep() {
  local pattern="$1" file="$2"
  if grep -Eq "$pattern" "$file"; then
    fail "forbidden pattern found in $file: $pattern"
  fi
}

run_install() {
  bash "$INSTALL" --no-color "$@"
}

test_default_claude_track_a() {
  local target="$TMP_DIR/claude-a"
  run_install --target "$target" --force --only code-implement --codex-track claude
  assert_file "$target/code-implement/SKILL.md"
  assert_not_exists "$target/code-implement/SKILL.claude.md"
  assert_not_exists "$target/code-implement/SKILL.codex.md"
  assert_grep 'Track A' "$target/code-implement/SKILL.md"
}

test_claude_track_b_preserved() {
  local target="$TMP_DIR/claude-b"
  local out="$TMP_DIR/claude-b.out"
  run_install --target "$target" --dry-run --force --only code-implement --codex-track codex >"$out"
  assert_not_exists "$target"
  assert_grep 'track=codex' "$out"
  assert_grep 'SKILL\.codex\.md .* SKILL\.md' "$out"
}

test_codex_runtime_single_model() {
  local target="$TMP_DIR/codex"
  run_install --runtime codex --target "$target" --force --only code-implement
  assert_file "$target/code-implement/SKILL.md"
  assert_not_exists "$target/code-implement/SKILL.openai.md"
  assert_not_exists "$target/code-implement/SKILL.claude.md"
  assert_not_exists "$target/code-implement/SKILL.codex.md"
  assert_grep 'Codex-native' "$target/code-implement/SKILL.md"
  assert_no_grep 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' "$target/code-implement/SKILL.md"
}

test_codex_runtime_rejects_codex_track() {
  local target="$TMP_DIR/invalid"
  local out="$TMP_DIR/ser-invalid.out"
  local err="$TMP_DIR/ser-invalid.err"
  if run_install --runtime codex --target "$target" --dry-run --codex-track codex --only code-implement >"$out" 2>"$err"; then
    fail "expected --runtime codex --codex-track codex to fail"
  fi
  grep -Eq -- '--codex-track.*runtime codex|runtime codex.*--codex-track' "$err" || {
    cat "$err" >&2
    fail "missing invalid runtime/track error"
  }
}

test_codex_runtime_default_target() {
  local out="$TMP_DIR/default-target.out"
  (
    cd "$REPO_ROOT"
    bash "$INSTALL" --no-color --runtime codex --dry-run --force --only code-review >"$out"
  )
  assert_grep "Target : ${REPO_ROOT}/\\.agents/skills" "$out"
  assert_grep 'would install .*code-review' "$out"
}

test_default_claude_track_a
test_claude_track_b_preserved
test_codex_runtime_single_model
test_codex_runtime_rejects_codex_track
test_codex_runtime_default_target

echo "[PASS] install-skills runtime tests"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
bash scripts/test_install_skills.sh
```

Expected: FAIL because `--runtime` is not recognized or `SKILL.openai.md` does not exist.

- [ ] **Step 3: Commit failing test scaffold**

```bash
git add scripts/test_install_skills.sh
git commit -m "test: cover installer runtime selection"
```

---

### Task 2: Add Installer Runtime Axis

**Files:**
- Modify: `scripts/install-skills.sh`
- Test: `scripts/test_install_skills.sh`

- [ ] **Step 1: Update installer help and defaults**

Modify the option header in `scripts/install-skills.sh` so it includes:

```bash
#       --runtime R       Select runtime: 'claude' (default) or 'codex'.
#                         'claude' installs to ./.claude/skills and supports
#                         --codex-track claude|codex.
#                         'codex' installs to ./.agents/skills, selects
#                         SKILL.openai.md > SKILL.md, and rejects --codex-track.
```

Change defaults near the top to:

```bash
RUNTIME="claude"      # claude | codex
TARGET_DIR=""
TARGET_SET=0
USER_TARGET=0
CODEX_TRACK="claude"
CODEX_TRACK_SET=0
```

- [ ] **Step 2: Parse `--runtime` and track explicit target flags**

In argument parsing:

```bash
-t|--target)    [ $# -ge 2 ] || { log_error "--target requires an argument"; exit 1; }
                TARGET_DIR="$2"; TARGET_SET=1; shift 2 ;;
--user)         TARGET_DIR="${HOME}/.claude/skills"; TARGET_SET=1; USER_TARGET=1; shift ;;
--runtime)      [ $# -ge 2 ] || { log_error "--runtime requires an argument"; exit 1; }
                case "$2" in
                  claude|codex) RUNTIME="$2" ;;
                  *) log_error "--runtime must be 'claude' or 'codex' (got: $2)"; exit 1 ;;
                esac
                shift 2 ;;
--codex-track)  [ $# -ge 2 ] || { log_error "--codex-track requires an argument"; exit 1; }
                CODEX_TRACK_SET=1
                case "$2" in
                  claude|codex) CODEX_TRACK="$2" ;;
                  *) log_error "--codex-track must be 'claude' or 'codex' (got: $2)"; exit 1 ;;
                esac
                shift 2 ;;
```

- [ ] **Step 3: Validate runtime combinations and set default targets**

After parsing and before `abspath`:

```bash
if [ "$RUNTIME" = "codex" ]; then
  if [ "$CODEX_TRACK_SET" -eq 1 ]; then
    log_error "--codex-track is only valid with --runtime claude; Codex runtime is single-model."
    exit 1
  fi
  if [ "$USER_TARGET" -eq 1 ]; then
    log_error "--user is not supported with --runtime codex in this version; use --target explicitly."
    exit 1
  fi
fi

if [ "$TARGET_SET" -eq 0 ]; then
  case "$RUNTIME" in
    claude) TARGET_DIR="${REPO_ROOT}/.claude/skills" ;;
    codex)  TARGET_DIR="${REPO_ROOT}/.agents/skills" ;;
  esac
fi
```

- [ ] **Step 4: Discover `SKILL.openai.md`**

Update `discover_skills` find expression:

```bash
find "$SOURCE_DIR" -type f \
  \( -name 'SKILL.md' -o -name 'SKILL.claude.md' -o -name 'SKILL.codex.md' -o -name 'SKILL.openai.md' \) \
  -print0 | sort -z
```

- [ ] **Step 5: Implement runtime-specific variant selection**

Inside `install_one`, replace the variant detection block with:

```bash
local has_plain=0 has_variant=0 variant_file="" selected_file="" materialize_variant=0
[ -f "$src/SKILL.md" ] && has_plain=1

if [ "$RUNTIME" = "codex" ]; then
  if [ -f "$src/SKILL.openai.md" ]; then
    selected_file="SKILL.openai.md"
    has_variant=1
    materialize_variant=1
  elif [ "$has_plain" -eq 1 ]; then
    selected_file="SKILL.md"
  else
    log_error "$name: Codex runtime requires SKILL.openai.md or runtime-neutral SKILL.md"
    return 1
  fi
else
  if [ -f "$src/SKILL.${CODEX_TRACK}.md" ]; then
    variant_file="SKILL.${CODEX_TRACK}.md"
    has_variant=1
  fi
  if [ "$has_plain" -eq 0 ] && [ "$has_variant" -eq 0 ]; then
    if [ -f "$src/SKILL.claude.md" ]; then
      variant_file="SKILL.claude.md"
      has_variant=1
      log_warn "$name: no SKILL.${CODEX_TRACK}.md; falling back to SKILL.claude.md"
    elif [ -f "$src/SKILL.codex.md" ]; then
      variant_file="SKILL.codex.md"
      has_variant=1
      log_warn "$name: no SKILL.${CODEX_TRACK}.md; falling back to SKILL.codex.md"
    fi
  fi
  if [ "$has_variant" -eq 1 ] && [ "$has_plain" -eq 0 ]; then
    selected_file="$variant_file"
    materialize_variant=1
  else
    selected_file="SKILL.md"
  fi
fi
```

Update copy exclusions in materialized variant mode:

```bash
--exclude='SKILL.claude.md' --exclude='SKILL.codex.md' --exclude='SKILL.openai.md'
```

and:

```bash
rm -f "$dst/SKILL.claude.md" "$dst/SKILL.codex.md" "$dst/SKILL.openai.md"
cp "$src/$selected_file" "$dst/SKILL.md"
```

- [ ] **Step 6: Update logging**

Replace the current `log_info "Codex  : track=$CODEX_TRACK"` with:

```bash
log_info "Runtime: $RUNTIME"
if [ "$RUNTIME" = "claude" ]; then
  log_info "Track  : $CODEX_TRACK"
else
  log_info "Track  : single-model"
fi
```

- [ ] **Step 7: Run installer tests**

Run:

```bash
bash scripts/test_install_skills.sh
```

Expected: still FAIL because `SKILL.openai.md` files and audit are not implemented.

- [ ] **Step 8: Commit installer runtime axis**

```bash
git add scripts/install-skills.sh
git commit -m "feat: add installer runtime axis"
```

---

### Task 3: Add Codex-Native Skill Variants

**Files:**
- Create: `skills/code-implement/SKILL.openai.md`
- Create: `skills/code-review/SKILL.openai.md`
- Create: `skills/writing-review/SKILL.openai.md`
- Create: `skills/idea-verify/SKILL.openai.md`
- Create: `skills/project-integrate/SKILL.openai.md`
- Test: `scripts/test_install_skills.sh`

- [ ] **Step 1: Create `code-implement` Codex variant**

Create `skills/code-implement/SKILL.openai.md` by adapting `SKILL.claude.md` with these exact semantic changes:

```markdown
# code-implement (Codex-native single-model)

**Trigger**: User wants to write new code or modify existing code.

**Shared context**: None at this stage; if a roadmap is used, that file carries the spec.

**Runtime**: Codex-native. The active Codex session implements directly with strict TDD. Do not delegate to `/codex:*` commands.
```

Also replace the SER-framework guard row with:

```markdown
| Change touches SER framework (`.agents/`, `skills/`, `config.yaml`, `AGENTS.md`) | **Small + Codex handles directly** -> Step 2 |
```

Keep the rest of the Track A TDD and roadmap workflow intact. Replace output tag:

```text
[code-implement / codex-native] {small|roadmap} execution complete
```

- [ ] **Step 2: Create `code-review` Codex variant**

Create `skills/code-review/SKILL.openai.md` by adapting `SKILL.claude.md` with:

```markdown
# code-review (Codex-native single-reviewer)

**Runtime**: Codex-native. The active Codex session performs a single-reviewer plan-compliance and quality review. Do not invoke `/codex:review`.
```

Replace reviewer labels with:

```markdown
**Reviewer**: Codex-native single reviewer
```

Remove the architectural note that Track B adds `/codex:review`. Replace it with:

```markdown
## Architectural Note

Codex-native review is single-model by design. It checks plan compliance, test evidence, unplanned changes, and obvious logic risks in one pass. Users who need independent dual-model review should run a separate external review workflow outside this runtime.
```

- [ ] **Step 3: Create `writing-review` Codex variant**

Create `skills/writing-review/SKILL.openai.md` from `SKILL.claude.md` with:

```markdown
# writing-review (Codex-native single-reviewer)

**Runtime**: Codex-native. Produce one rigorous simulated peer review directly. Do not call subagents, `/codex:*`, or cross-model MCP reviewers.
```

Keep the same review dimensions and output format as Track A. Replace any “Claude subagent” or “external reviewer” language with “single Codex-native reviewer”.

- [ ] **Step 4: Create `idea-verify` Codex variant**

Create `skills/idea-verify/SKILL.openai.md` from `SKILL.claude.md` with:

```markdown
# idea-verify (Codex-native single-model)

**Runtime**: Codex-native. Verify novelty by combining hard sources and the active Codex session's analysis. Do not use `/codex:*`, `mcp__codex__codex`, or a second model reviewer.
```

Keep DBLP/arXiv evidence collection and final verdict structure. Replace “Claude subagent” with “Codex analysis”.

- [ ] **Step 5: Create `project-integrate` Codex variant**

Create `skills/project-integrate/SKILL.openai.md` from `SKILL.md` with these replacements:

```text
CLAUDE.md -> AGENTS.md
.claude/ -> .agents/
.claude/skills -> .agents/skills
Claude Code -> Codex
```

Keep the conflict inventory, merge discipline, and verification workflow intact. The hook-specific references to `.claude/hooks/ser-intent-router.sh` must be removed because Codex-native installation is skill-driven via `.agents/skills` and root `AGENTS.md`.

- [ ] **Step 6: Run tests**

Run:

```bash
bash scripts/test_install_skills.sh
```

Expected: Codex runtime selection tests pass for `code-implement`; audit coverage may still fail after Task 4.

- [ ] **Step 7: Commit Codex-native variants**

```bash
git add skills/code-implement/SKILL.openai.md skills/code-review/SKILL.openai.md skills/writing-review/SKILL.openai.md skills/idea-verify/SKILL.openai.md skills/project-integrate/SKILL.openai.md
git commit -m "feat: add Codex-native skill variants"
```

---

### Task 4: Add Codex Runtime Audit

**Files:**
- Modify: `scripts/install-skills.sh`
- Test: `scripts/test_install_skills.sh`

- [ ] **Step 1: Add forbidden marker configuration**

Add near helper functions:

```bash
CODEX_FORBIDDEN_MARKERS='Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex'
```

- [ ] **Step 2: Add audit function**

Add:

```bash
audit_codex_skill_file() {
  local name="$1" file="$2"
  if [ "$RUNTIME" != "codex" ]; then
    return 0
  fi
  if grep -Eq "$CODEX_FORBIDDEN_MARKERS" "$file"; then
    log_error "$name: Codex runtime coupling found in $(basename "$file")"
    grep -En "$CODEX_FORBIDDEN_MARKERS" "$file" >&2 || true
    return 1
  fi
  return 0
}
```

- [ ] **Step 3: Audit selected source before install**

After `selected_file` is set in `install_one`, before dry-run handling:

```bash
if ! audit_codex_skill_file "$name" "$src/$selected_file"; then
  return 1
fi
```

- [ ] **Step 4: Run Codex dry-run audit**

Run:

```bash
bash scripts/install-skills.sh --dry-run --runtime codex --no-color
```

Expected: FAIL with a concrete list of runtime-coupled skills that still need `SKILL.openai.md` or source neutralization.

- [ ] **Step 5: Add variants or neutralize sources for every audit failure**

For every failure emitted by Step 4:

1. If the skill's behavior is platform-specific, create `skills/{name}/SKILL.openai.md`.
2. If the source `SKILL.md` only mentions Claude Code in a generic path example, rewrite it to a runtime-neutral phrase.
3. Re-run the dry-run audit.

The step is complete only when:

```bash
bash scripts/install-skills.sh --dry-run --runtime codex --no-color
```

exits 0.

- [ ] **Step 6: Run installer tests**

Run:

```bash
bash scripts/test_install_skills.sh
```

Expected: PASS.

- [ ] **Step 7: Commit audit and remaining variant fixes**

```bash
git add scripts/install-skills.sh scripts/test_install_skills.sh skills
git commit -m "feat: audit Codex-native skill installs"
```

---

### Task 5: Add Codex Root Instructions

**Files:**
- Create: `AGENTS.md`
- Test: `scripts/install-skills.sh`

- [ ] **Step 1: Create root `AGENTS.md`**

Create `AGENTS.md` with these sections:

```markdown
# AGENTS.md — SER Codex Runtime

You are running SER inside Codex.

SER is a behavior-driven research collaboration framework. It routes natural-language research requests to local skills under `.agents/skills/`, maintains project memory, tracks checklists, and can evolve skill instructions from session feedback.

## Runtime Rules

- Use Codex-native skills from `.agents/skills/`.
- Treat `AGENTS.md` as the root behavioral protocol.
- Do not depend on Claude Code runtime files, `.claude/skills`, `/codex:*` delegation commands, or `mcp__codex__codex`.
- Use the active Codex session as the single model for implementation, review, writing, and verification.

## Project Flow

1. Read `config.yaml` when present.
2. Read `memory/MEMORY.md` when present.
3. Use `Checklist.md` and `checklists/` as the progress source of truth.
4. Route user intent to the matching skill when a skill's description applies.
5. Write durable outputs to the project directories declared in this repository.

## Skill Loading

Installed Codex skills live in `.agents/skills/{skill-name}/SKILL.md`.

If a task matches a skill, follow that skill's instructions. If no specific skill applies, use `general-research` behavior: clarify the user's goal, gather evidence, and produce a concrete next action.

## Repository Boundaries

- Keep edits scoped to the active research project.
- Do not rewrite framework instructions unless the user asks to modify SER itself.
- Preserve user work and do not remove untracked files without explicit permission.
```

- [ ] **Step 2: Run Codex install**

Run:

```bash
bash scripts/install-skills.sh --runtime codex --force --no-color
```

Expected: installs to `.agents/skills` and exits 0.

- [ ] **Step 3: Audit installed skills**

Run:

```bash
rg 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' .agents/skills
```

Expected: no output.

- [ ] **Step 4: Commit root Codex instructions**

```bash
git add AGENTS.md
git commit -m "feat: add Codex root instructions"
```

---

### Task 6: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `scripts/README.md`
- Modify: `scripts/CLAUDE.md`

- [ ] **Step 1: Update README runtime section**

In `README.md`, add a section after the current skill install section:

````markdown
### Codex-native runtime

SER also supports a Codex-native single-model runtime.

```bash
bash scripts/install-skills.sh --runtime codex
codex
```

Codex-native installs write skills to `.agents/skills/` and use `AGENTS.md` as the root instruction file. This is separate from Claude Code `--codex-track codex`, which keeps Claude Code as the runtime and adds Codex as an extra reviewer/executor for selected skills.
````

- [ ] **Step 2: Update Chinese README**

Add the equivalent Chinese section:

````markdown
### Codex 原生运行时

SER 也支持 Codex 原生单模型运行时。

```bash
bash scripts/install-skills.sh --runtime codex
codex
```

Codex 原生安装会把技能写入 `.agents/skills/`，并使用 `AGENTS.md` 作为根行为协议。它不同于 Claude Code 的 `--codex-track codex`：后者仍以 Claude Code 为运行时，只是在部分技能里增加 Codex 作为额外执行器或评审者。
````

- [ ] **Step 3: Update scripts docs**

In `scripts/README.md`, document:

```markdown
bash scripts/install-skills.sh --runtime claude --codex-track claude
bash scripts/install-skills.sh --runtime claude --codex-track codex
bash scripts/install-skills.sh --runtime codex
```

In `scripts/CLAUDE.md`, update the `install-skills.sh` row to include `--runtime claude|codex`.

- [ ] **Step 4: Run Markdown grep checks**

Run:

```bash
rg -n 'Codex-native|Codex 原生|--runtime codex|\.agents/skills|AGENTS\.md' README.md README.zh-CN.md scripts/README.md scripts/CLAUDE.md
```

Expected: each file has at least one relevant hit.

- [ ] **Step 5: Commit docs**

```bash
git add README.md README.zh-CN.md scripts/README.md scripts/CLAUDE.md
git commit -m "docs: document Codex-native runtime"
```

---

### Task 7: Final Verification

**Files:**
- No new files.

- [ ] **Step 1: Run Claude runtime dry-runs**

Run:

```bash
bash scripts/install-skills.sh --dry-run --runtime claude --codex-track claude --no-color
bash scripts/install-skills.sh --dry-run --runtime claude --codex-track codex --no-color
```

Expected: both exit 0.

- [ ] **Step 2: Run Codex runtime dry-run and install**

Run:

```bash
bash scripts/install-skills.sh --dry-run --runtime codex --no-color
bash scripts/install-skills.sh --runtime codex --force --no-color
```

Expected: both exit 0.

- [ ] **Step 3: Run install tests**

Run:

```bash
bash scripts/test_install_skills.sh
```

Expected: PASS.

- [ ] **Step 4: Confirm Codex installed-surface audit**

Run:

```bash
rg 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' .agents/skills
```

Expected: no output.

- [ ] **Step 5: Confirm Git state**

Run:

```bash
git status --short --branch
git log --oneline --max-count=8
```

Expected: branch is `feat/codex-native-runtime`; only pre-existing untracked user files remain outside committed implementation.

- [ ] **Step 6: Final commit if verification changed generated install tree intentionally**

The `.agents/skills` install output is generated project-local state. Do not commit it unless the repository already tracks generated installed skills. Confirm:

```bash
git status --short
```

Expected: no tracked implementation changes remain unstaged. Pre-existing untracked files may remain.
