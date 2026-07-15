#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="${REPO_ROOT}/scripts/install-skills.sh"
TMP_DIR="$(mktemp -d)"
SINGLE_MODEL_SKILLS=(code-implement code-review idea-verify writing-review)
FORBIDDEN_SINGLE_MODEL_MARKERS='--codex-track|/codex:review|/codex:rescue|mcp__codex__codex'

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
  grep -Eq -- "$pattern" "$file" || fail "pattern not found in $file: $pattern"
}

assert_no_grep() {
  local pattern="$1" file="$2"
  if grep -Eq -- "$pattern" "$file"; then
    fail "forbidden pattern found in $file: $pattern"
  fi
}

assert_no_tree_grep() {
  local pattern="$1" root="$2"
  if grep -RInE -- "$pattern" "$root"; then
    fail "forbidden pattern found under $root: $pattern"
  fi
}

assert_single_model_skills_installed() {
  local target="$1" runtime="$2" skill source_variant
  for skill in "${SINGLE_MODEL_SKILLS[@]}"; do
    assert_file "$target/$skill/SKILL.md"
    assert_not_exists "$target/$skill/SKILL.claude.md"
    assert_not_exists "$target/$skill/SKILL.codex.md"
    assert_not_exists "$target/$skill/SKILL.openai.md"
    case "$runtime" in
      claude) source_variant="$REPO_ROOT/skills/$skill/SKILL.claude.md" ;;
      codex) source_variant="$REPO_ROOT/skills/$skill/SKILL.openai.md" ;;
      *) fail "unsupported runtime for single-model assertion: $runtime" ;;
    esac
    cmp -s "$source_variant" "$target/$skill/SKILL.md" ||
      fail "installed $skill/SKILL.md does not match $source_variant"
  done
}

assert_valid_skill_frontmatter_tree() {
  local root="$1"
  python3 - "$root" <<'PY'
from pathlib import Path
import sys

import yaml

root = Path(sys.argv[1])
bad = []

for path in sorted(root.rglob("SKILL.md")):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        bad.append(f"{path}: missing YAML frontmatter delimited by ---")
        continue
    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        bad.append(f"{path}: missing closing YAML frontmatter delimiter")
        continue
    try:
        data = yaml.safe_load(frontmatter)
    except Exception as exc:
        bad.append(f"{path}: invalid YAML frontmatter: {exc}")
        continue
    if not isinstance(data, dict):
        bad.append(f"{path}: YAML frontmatter must be a mapping")
        continue
    for key in ("name", "description"):
        if not data.get(key):
            bad.append(f"{path}: YAML frontmatter missing {key}")

if bad:
    print("\n".join(bad), file=sys.stderr)
    sys.exit(1)
PY
}

run_install() {
  bash "$INSTALL" --no-color "$@"
}

test_source_tree_has_no_cross_model_tracks() {
  local skill
  for skill in "${SINGLE_MODEL_SKILLS[@]}"; do
    assert_not_exists "$REPO_ROOT/skills/$skill/SKILL.codex.md"
  done
  assert_not_exists "$REPO_ROOT/skills/_shared/codex-contract.md"
  assert_not_exists "$REPO_ROOT/skills/_shared/cross-model-review.md"
}

test_codex_runtime_audits_copied_auxiliary_files() {
  local source="$TMP_DIR/audit-aux-source"
  local target="$TMP_DIR/audit-aux-target"
  local out="$TMP_DIR/audit-aux.out"
  local err="$TMP_DIR/audit-aux.err"

  mkdir -p "$source/audit-aux"
  printf '%s\n' \
    '---' \
    'name: audit-aux' \
    'description: Clean Codex-native test skill.' \
    '---' \
    '# Audit auxiliary files' >"$source/audit-aux/SKILL.openai.md"
  printf '%s\n' 'This auxiliary file requires Claude Code.' >"$source/audit-aux/NOTES.md"

  if run_install --runtime codex --source "$source" --target "$target" \
    --only audit-aux >"$out" 2>"$err"; then
    fail "expected Codex runtime audit to reject a copied auxiliary file"
  fi
  assert_not_exists "$target/audit-aux"
  assert_grep 'NOTES\.md' "$err"
  assert_grep 'Claude Code' "$err"
}

test_codex_runtime_rejects_copied_auxiliary_symlinks() {
  local source="$TMP_DIR/audit-symlink-source"
  local target="$TMP_DIR/audit-symlink-target"
  local payload="$TMP_DIR/audit-symlink-payload.txt"
  local out="$TMP_DIR/audit-symlink.out"
  local err="$TMP_DIR/audit-symlink.err"

  mkdir -p "$source/audit-symlink"
  printf '%s\n' \
    '---' \
    'name: audit-symlink' \
    'description: Clean Codex-native symlink audit test skill.' \
    '---' \
    '# Audit auxiliary symlinks' >"$source/audit-symlink/SKILL.openai.md"
  printf '%s\n' 'This external payload requires Claude Code.' >"$payload"
  ln -s "$payload" "$source/audit-symlink/NOTES.md"

  if run_install --runtime codex --source "$source" --target "$target" \
    --only audit-symlink >"$out" 2>"$err"; then
    fail "expected Codex runtime audit to reject a copied auxiliary symlink"
  fi
  assert_not_exists "$target/audit-symlink"
  assert_grep 'symlink' "$err"
  assert_grep 'NOTES\.md' "$err"
}

test_single_model_surface_omits_cross_model_controls() {
  local help_out="$TMP_DIR/install-help.out"
  run_install --help >"$help_out"
  assert_no_grep "$FORBIDDEN_SINGLE_MODEL_MARKERS" "$help_out"
  assert_no_grep "$FORBIDDEN_SINGLE_MODEL_MARKERS" "$INSTALL"
  assert_no_tree_grep "$FORBIDDEN_SINGLE_MODEL_MARKERS" "$REPO_ROOT/skills"
}

test_claude_runtime_single_model() {
  local target="$TMP_DIR/claude"
  run_install --runtime claude --target "$target" --force \
    --only code-implement,code-review,idea-verify,writing-review
  assert_single_model_skills_installed "$target" claude
  assert_no_tree_grep "$FORBIDDEN_SINGLE_MODEL_MARKERS" "$target"
  assert_no_tree_grep 'Codex|codex' "$target"
  assert_valid_skill_frontmatter_tree "$target"
}

test_default_runtime_is_claude() {
  local target="$TMP_DIR/default-claude"
  run_install --target "$target" --force \
    --only code-implement,code-review,idea-verify,writing-review
  assert_single_model_skills_installed "$target" claude
  assert_no_tree_grep 'Codex|codex' "$target"
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

test_codex_runtime_ignores_claude_only_skills() {
  local source="$TMP_DIR/claude-only-source"
  local out="$TMP_DIR/claude-only-list.out"

  mkdir -p "$source/claude-only"
  printf '%s\n' '---' 'name: claude-only' 'description: Claude-only skill.' '---' >"$source/claude-only/SKILL.claude.md"

  run_install --runtime codex --source "$source" --list >"$out"
  assert_no_grep 'claude-only' "$out"
}

test_codex_runtime_single_model() {
  local target="$TMP_DIR/codex"
  run_install --runtime codex --target "$target" --force --only experiment-run
  assert_file "$target/experiment-run/SKILL.md"
  assert_not_exists "$target/experiment-run/SKILL.openai.md"
  assert_not_exists "$target/experiment-run/SKILL.claude.md"
  assert_not_exists "$target/experiment-run/SKILL.codex.md"
  assert_grep 'Codex-native' "$target/experiment-run/SKILL.md"
  assert_no_grep 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' "$target/experiment-run/SKILL.md"
}

test_codex_runtime_installed_surface_is_clean() {
  local target="$TMP_DIR/codex-surface"
  run_install --runtime codex --target "$target" --force
  assert_dir "$target"
  assert_not_exists "$target/fey-r/README.md"
  assert_not_exists "$target/fey-r/.gitignore"
  assert_not_exists "$target/fey-r/.git"
  assert_no_tree_grep 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' "$target"
  assert_valid_skill_frontmatter_tree "$target"
  assert_single_model_skills_installed "$target" codex
  local legacy consolidated
  for legacy in code-roadmap idea-refine paper-art; do
    assert_not_exists "$target/$legacy"
  done
  for consolidated in checklist code idea memory paper-assets proof theory writing; do
    assert_dir "$target/$consolidated"
  done
}

test_codex_runtime_rejects_link() {
  local target="$TMP_DIR/invalid-link"
  local out="$TMP_DIR/ser-invalid-link.out"
  local err="$TMP_DIR/ser-invalid-link.err"
  if run_install --runtime codex --target "$target" --link --dry-run --only fey-r >"$out" 2>"$err"; then
    fail "expected --runtime codex --link to fail"
  fi
  grep -Eq -- '--link.*--runtime codex|--runtime codex.*--link|Codex runtime.*link' "$err" || {
    cat "$err" >&2
    fail "missing invalid codex link error"
  }
  assert_not_exists "$target"
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
    bash "$INSTALL" --no-color --runtime codex --dry-run --force --only experiment-run >"$out"
  )
  assert_grep "Target : ${REPO_ROOT}/\\.agents/skills" "$out"
  assert_grep 'would (install|update) .*experiment-run' "$out"
}

test_source_tree_has_no_cross_model_tracks
test_codex_runtime_audits_copied_auxiliary_files
test_codex_runtime_rejects_copied_auxiliary_symlinks
test_single_model_surface_omits_cross_model_controls
test_claude_runtime_single_model
test_default_runtime_is_claude
test_claude_runtime_ignores_openai_only_skills
test_claude_runtime_does_not_leak_openai_variant
test_codex_runtime_ignores_claude_only_skills
test_codex_runtime_single_model
test_codex_runtime_installed_surface_is_clean
test_codex_runtime_rejects_link
test_codex_runtime_audits_selected_skill_source
test_codex_runtime_skips_existing_target_before_audit
test_codex_runtime_default_target

echo "[PASS] install-skills runtime tests"
