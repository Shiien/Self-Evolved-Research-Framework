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
