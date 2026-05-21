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

test_claude_runtime_ignores_openai_only_skills() {
  local source="$TMP_DIR/openai-source"
  local claude_target="$TMP_DIR/openai-claude"
  local codex_target="$TMP_DIR/openai-codex"
  local list_out="$TMP_DIR/openai-claude-list.out"
  local codex_dry_out="$TMP_DIR/openai-codex-dry.out"

  mkdir -p "$source/openai-only"
  printf '# OpenAI only\n' >"$source/openai-only/SKILL.openai.md"

  run_install --runtime claude --source "$source" --list >"$list_out"
  assert_no_grep 'openai-only' "$list_out"

  run_install --runtime claude --source "$source" --target "$claude_target" --force
  assert_not_exists "$claude_target/openai-only"

  run_install --runtime codex --source "$source" --target "$codex_target" --dry-run --force >"$codex_dry_out"
  assert_grep 'runtime=codex' "$codex_dry_out"
  assert_grep 'SKILL\.openai\.md -> SKILL\.md' "$codex_dry_out"

  run_install --runtime codex --source "$source" --target "$codex_target" --force
  assert_file "$codex_target/openai-only/SKILL.md"
  assert_grep 'OpenAI only' "$codex_target/openai-only/SKILL.md"
  assert_not_exists "$codex_target/openai-only/SKILL.openai.md"
}

test_claude_runtime_does_not_leak_openai_variant() {
  local source="$TMP_DIR/mixed-source"
  local target="$TMP_DIR/mixed-claude"

  mkdir -p "$source/mixed"
  printf '# Claude neutral\n' >"$source/mixed/SKILL.md"
  printf '# OpenAI variant\n' >"$source/mixed/SKILL.openai.md"

  run_install --runtime claude --source "$source" --target "$target" --force
  assert_file "$target/mixed/SKILL.md"
  assert_grep 'Claude neutral' "$target/mixed/SKILL.md"
  assert_not_exists "$target/mixed/SKILL.openai.md"
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

test_codex_runtime_audits_selected_skill_source() {
  local source="$TMP_DIR/audit-source"
  local claude_target="$TMP_DIR/audit-claude"
  local codex_target="$TMP_DIR/audit-codex"
  local out="$TMP_DIR/audit-codex.out"
  local err="$TMP_DIR/audit-codex.err"

  mkdir -p "$source/audit-bad"
  printf '# Audit bad\n\nMentions Claude Code in the selected source.\n' >"$source/audit-bad/SKILL.md"

  run_install --runtime claude --source "$source" --target "$claude_target" --force
  assert_file "$claude_target/audit-bad/SKILL.md"

  if run_install --runtime codex --source "$source" --target "$codex_target" --dry-run --force >"$out" 2>"$err"; then
    fail "expected Codex runtime audit to reject forbidden markers"
  fi
  assert_grep 'audit-bad: Codex runtime coupling found in SKILL\.md' "$err"
  assert_grep 'Claude Code' "$err"
  assert_not_exists "$codex_target"
}

test_codex_runtime_skips_existing_target_before_audit() {
  local source="$TMP_DIR/audit-skip-source"
  local target="$TMP_DIR/audit-skip-target"
  local out="$TMP_DIR/audit-skip.out"
  local err="$TMP_DIR/audit-skip.err"

  mkdir -p "$source/audit-skip" "$target/audit-skip"
  printf '# Already installed\n\nClean Codex-native content.\n' >"$target/audit-skip/SKILL.md"
  printf '# Audit skip\n\nMentions Claude Code in the selected source.\n' >"$source/audit-skip/SKILL.md"

  run_install --runtime codex --source "$source" --target "$target" >"$out" 2>"$err"
  assert_grep 'audit-skip \(already installed' "$out"
  assert_no_grep 'Codex runtime coupling found' "$err"
  assert_grep 'Clean Codex-native content' "$target/audit-skip/SKILL.md"
  assert_no_grep 'Claude Code' "$target/audit-skip/SKILL.md"
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
test_claude_runtime_ignores_openai_only_skills
test_claude_runtime_does_not_leak_openai_variant
test_codex_runtime_single_model
test_codex_runtime_rejects_codex_track
test_codex_runtime_audits_selected_skill_source
test_codex_runtime_skips_existing_target_before_audit
test_codex_runtime_default_target

echo "[PASS] install-skills runtime tests"
