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
  run_install --target "$target" --force --only code-implement --codex-track codex
  assert_file "$target/code-implement/SKILL.md"
  assert_not_exists "$target/code-implement/SKILL.claude.md"
  assert_not_exists "$target/code-implement/SKILL.codex.md"
  assert_grep 'Track B' "$target/code-implement/SKILL.md"
  assert_grep '/codex:rescue' "$target/code-implement/SKILL.md"
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
  if run_install --runtime codex --target "$target" --dry-run --codex-track codex --only code-implement >/tmp/ser-invalid.out 2>/tmp/ser-invalid.err; then
    fail "expected --runtime codex --codex-track codex to fail"
  fi
  grep -Eq -- '--codex-track.*runtime codex|runtime codex.*--codex-track' /tmp/ser-invalid.err || {
    cat /tmp/ser-invalid.err >&2
    fail "missing invalid runtime/track error"
  }
}

test_codex_runtime_default_target() {
  local project="$TMP_DIR/project"
  mkdir -p "$project"
  (
    cd "$REPO_ROOT"
    bash "$INSTALL" --no-color --runtime codex --force --only code-review
  )
  assert_dir "$REPO_ROOT/.agents/skills/code-review"
  assert_file "$REPO_ROOT/.agents/skills/code-review/SKILL.md"
  rm -rf "$REPO_ROOT/.agents/skills/code-review"
  rmdir "$REPO_ROOT/.agents/skills" "$REPO_ROOT/.agents" 2>/dev/null || true
}

test_default_claude_track_a
test_claude_track_b_preserved
test_codex_runtime_single_model
test_codex_runtime_rejects_codex_track
test_codex_runtime_default_target

echo "[PASS] install-skills runtime tests"
