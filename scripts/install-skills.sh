#!/usr/bin/env bash
# install-skills.sh — Install bundled skills for one selected model runtime
#
# Auto-discovers every directory containing a runtime-neutral or runtime-native
# skill manifest under the source tree (default: ./skills), then installs each
# skill for either Claude or Codex. Each runtime selects its own native manifest.
#
# Directories without a manifest accepted by the selected runtime (e.g.
# skills/_shared and skills/td-nl) are ignored as SER infrastructure.
#
# Safe to run multiple times. Existing installs are skipped unless --force.
#
# ─────────────────────────────────────────────────────────────────────────────
# Usage:
#   bash scripts/install-skills.sh [options]
#
# Options:
#   -h, --help            Show this help and exit
#   -n, --dry-run         Print actions without modifying the filesystem
#   -f, --force           Overwrite existing skills at the target
#   -l, --link            Symlink runtime-neutral SKILL.md skills for Claude.
#                         Claude-native manifests and all Codex skills are
#                         materialized as copies.
#   -s, --source DIR      Source directory to scan (default: ./skills)
#   -t, --target DIR      Target directory            (default depends on runtime)
#       --user            Shortcut for --target ~/.claude/skills (Claude only)
#       --runtime R       Select runtime: 'claude' (default) or 'codex'.
#                         Claude installs to ./.claude/skills and selects
#                         SKILL.claude.md > SKILL.md.
#                         Codex installs to ./.agents/skills and selects
#                         SKILL.openai.md > SKILL.md.
#       --only PATTERNS   Install only skills matching PATTERNS (comma-separated,
#                         glob supported; e.g. 'paper-*,code-*').
#                         Repeatable; union of all patterns is kept.
#       --exclude PATTERNS  Skip skills matching PATTERNS (comma-separated, glob
#                         supported; e.g. 'proof-*,theory-generalize'). Applied
#                         after --only. Repeatable; union of all patterns.
#       --list            List discovered skills (after --only/--exclude filters)
#                         and exit without installing
#       --no-color        Disable ANSI color output
#
# Selection examples:
#   --only 'paper-*'                       # all paper-* skills
#   --only paper-read,writing-draft        # pick two skills
#   --exclude 'theory-*,proof-*'           # drop theory + proof families
#   --only 'paper-*' --exclude paper-index # paper-* minus paper-index
#   --runtime claude --only 'code-*'       # Claude-native code skills
#   --runtime codex --only 'code-*'        # Codex-native code skills
#
# Exit codes:
#   0  success (or nothing to do)
#   1  argument / usage error
#   2  source directory invalid
#   3  one or more skills failed to install
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# --- Defaults ------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/skills"
RUNTIME="claude"      # claude | codex
TARGET_DIR=""
TARGET_SET=0
USER_TARGET=0
MODE="copy"          # copy | link
DRY_RUN=0
FORCE=0
LIST_ONLY=0
USE_COLOR=1
ONLY_PATTERNS=()
EXCLUDE_PATTERNS=()

# --- Helpers -------------------------------------------------------------------
CODEX_FORBIDDEN_MARKERS='Claude Code|\.claude|CLAUDE\.md|/co''dex:|mcp__co''dex__codex'

if [ -t 1 ]; then :; else USE_COLOR=0; fi

color() {
  # $1 = color name, $2... = message
  local c="$1"; shift
  if [ "$USE_COLOR" -eq 0 ]; then
    printf '%s' "$*"
    return
  fi
  case "$c" in
    red)    printf '\033[31m%s\033[0m' "$*" ;;
    green)  printf '\033[32m%s\033[0m' "$*" ;;
    yellow) printf '\033[33m%s\033[0m' "$*" ;;
    blue)   printf '\033[34m%s\033[0m' "$*" ;;
    dim)    printf '\033[2m%s\033[0m'  "$*" ;;
    *)      printf '%s' "$*" ;;
  esac
}

log_info()    { echo "$(color blue   '[*]') $*"; }
log_ok()      { echo "$(color green  '[+]') $*"; }
log_skip()    { echo "$(color dim    '[=]') $*"; }
log_warn()    { echo "$(color yellow '[!]') $*" >&2; }
log_error()   { echo "$(color red    '[x]') $*" >&2; }

audit_codex_skill_file() {
  local name="$1" file="$2" relative_file="$3"
  if [ "$RUNTIME" != "codex" ]; then
    return 0
  fi
  if grep -IEq -- "$CODEX_FORBIDDEN_MARKERS" "$file"; then
    log_error "$name: Codex runtime coupling found in $relative_file"
    grep -IEn -- "$CODEX_FORBIDDEN_MARKERS" "$file" >&2 || true
    return 1
  fi
  return 0
}

codex_skill_path_is_copied() {
  local relative_file="$1" selected_file="$2"
  case "$relative_file" in
    "$selected_file"|SKILL.md|SKILL.claude.md|SKILL.openai.md)
      return 1 ;;
    README.md|.gitignore|.git|.git/*)
      return 1 ;;
    *)
      return 0 ;;
  esac
}

audit_codex_skill_tree() {
  local name="$1" src="$2" selected_file="$3"
  local file relative_file failed=0
  if [ "$RUNTIME" != "codex" ]; then
    return 0
  fi

  # The selected runtime manifest is materialized as SKILL.md, so audit it
  # explicitly under its source-relative name.
  if ! audit_codex_skill_file "$name" "$src/$selected_file" "$selected_file"; then
    failed=1
  fi

  # Audit every other file that survives the Codex copy. Root-level runtime
  # manifests are either selected above or omitted, while fey-r's
  # repository-only auxiliaries are removed from Codex installations. Reject
  # copied symlinks so the installed skill remains self-contained.
  while IFS= read -r -d '' file; do
    relative_file="${file#"$src/"}"
    if ! codex_skill_path_is_copied "$relative_file" "$selected_file"; then
      continue
    fi
    if [ -L "$file" ]; then
      log_error "$name: Codex runtime cannot copy symlink $relative_file; skills must be self-contained"
      failed=1
      continue
    fi
    if ! audit_codex_skill_file "$name" "$file" "$relative_file"; then
      failed=1
    fi
  done < <(find "$src" \( -type f -o -type l \) -print0)

  [ "$failed" -eq 0 ]
}

copy_runtime_aux_excludes() {
  if [ "$RUNTIME" = "codex" ]; then
    printf '%s\n' --exclude='/README.md' --exclude='/.gitignore' --exclude='/.git'
  fi
}

remove_runtime_aux_files() {
  local dst="$1"
  if [ "$RUNTIME" = "codex" ]; then
    rm -rf "$dst/README.md" "$dst/.gitignore" "$dst/.git"
  fi
}

usage() {
  # Print the header block (between the two ──── separators) as help text.
  awk '/^# ─{10,}/{n++; next} n==1' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

# --- Arg parsing ---------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)      usage 0 ;;
    -n|--dry-run)   DRY_RUN=1; shift ;;
    -f|--force)     FORCE=1; shift ;;
    -l|--link)      MODE="link"; shift ;;
    -s|--source)    [ $# -ge 2 ] || { log_error "--source requires an argument"; exit 1; }
                    SOURCE_DIR="$2"; shift 2 ;;
    -t|--target)    [ $# -ge 2 ] || { log_error "--target requires an argument"; exit 1; }
                    TARGET_DIR="$2"; TARGET_SET=1; shift 2 ;;
    --user)         TARGET_DIR="${HOME}/.claude/skills"; TARGET_SET=1; USER_TARGET=1; shift ;;
    --runtime)      [ $# -ge 2 ] || { log_error "--runtime requires an argument"; exit 1; }
                    case "$2" in
                      claude|codex) RUNTIME="$2" ;;
                      *) log_error "--runtime must be 'claude' or 'codex' (got: $2)"; exit 1 ;;
                    esac
                    shift 2 ;;
    --only)         [ $# -ge 2 ] || { log_error "--only requires an argument"; exit 1; }
                    IFS=',' read -r -a _tmp <<<"$2"
                    ONLY_PATTERNS+=("${_tmp[@]}")
                    shift 2 ;;
    --exclude)      [ $# -ge 2 ] || { log_error "--exclude requires an argument"; exit 1; }
                    IFS=',' read -r -a _tmp <<<"$2"
                    EXCLUDE_PATTERNS+=("${_tmp[@]}")
                    shift 2 ;;
    --list)         LIST_ONLY=1; shift ;;
    --no-color)     USE_COLOR=0; shift ;;
    --)             shift; break ;;
    -*)             log_error "Unknown option: $1"; usage 1 ;;
    *)              log_error "Unexpected argument: $1"; usage 1 ;;
  esac
done

if [ "$RUNTIME" = "codex" ]; then
  if [ "$USER_TARGET" -eq 1 ]; then
    log_error "--user is not supported with --runtime codex in this version; use --target explicitly."
    exit 1
  fi
  if [ "$MODE" = "link" ]; then
    log_error "--link is not supported with --runtime codex; Codex runtime requires materialized copies with runtime exclusions."
    exit 1
  fi
fi

if [ "$TARGET_SET" -eq 0 ]; then
  case "$RUNTIME" in
    claude) TARGET_DIR="${REPO_ROOT}/.claude/skills" ;;
    codex)  TARGET_DIR="${REPO_ROOT}/.agents/skills" ;;
  esac
fi

# Resolve to absolute paths (portable: no realpath required)
abspath() {
  local p="$1"
  case "$p" in
    /*) printf '%s' "$p" ;;
    *)  printf '%s/%s' "$(pwd)" "$p" ;;
  esac
}
SOURCE_DIR="$(abspath "$SOURCE_DIR")"
TARGET_DIR="$(abspath "$TARGET_DIR")"

# --- Validate source -----------------------------------------------------------
if [ ! -d "$SOURCE_DIR" ]; then
  log_error "Source directory not found: $SOURCE_DIR"
  exit 2
fi

# --- Discovery -----------------------------------------------------------------
# Find every directory that contains a manifest accepted by the selected
# runtime. Store (name, abs_path) pairs. "name" is the leaf directory name.
#
# Runtime-native manifests are materialized as SKILL.md at the target.
#
# We deliberately use `-print0` + null-delim read to be safe with unusual names.
discover_skills() {
  local roots=()
  # Match runtime-relevant skill manifests, then dedupe by directory.
  while IFS= read -r -d '' f; do
    roots+=("$f")
  done < <(
    if [ "$RUNTIME" = "codex" ]; then
      find "$SOURCE_DIR" -type f \
        \( -name 'SKILL.md' -o -name 'SKILL.openai.md' \) \
        -print0 | sort -z
    else
      find "$SOURCE_DIR" -type f \
        \( -name 'SKILL.md' -o -name 'SKILL.claude.md' \) \
        -print0 | sort -z
    fi
  )

  # Dedupe by directory — a directory may contain a neutral and a native
  # manifest, but it is still one skill.
  local seen_dirs=""
  for skill_md in "${roots[@]}"; do
    local skill_dir name
    skill_dir="$(dirname "$skill_md")"
    case " $seen_dirs " in
      *" $skill_dir "*) continue ;;
    esac
    seen_dirs="$seen_dirs $skill_dir"
    name="$(basename "$skill_dir")"
    printf '%s\t%s\n' "$name" "$skill_dir"
  done
}

mapfile -t DISCOVERED < <(discover_skills)

if [ "${#DISCOVERED[@]}" -eq 0 ]; then
  log_warn "No SKILL.md files found under $SOURCE_DIR — nothing to install."
  exit 0
fi

# --- Apply --only / --exclude filters ------------------------------------------
# Glob patterns match against the skill's leaf directory name.
name_matches_any() {
  local name="$1"; shift
  local p
  for p in "$@"; do
    # shellcheck disable=SC2053  # $p is a glob pattern, intentionally unquoted
    [[ $name == $p ]] && return 0
  done
  return 1
}

filter_discovered() {
  local mode="$1"; shift
  local filtered=()
  local entry name path
  for entry in "${DISCOVERED[@]}"; do
    IFS=$'\t' read -r name path <<<"$entry"
    if name_matches_any "$name" "$@"; then
      [ "$mode" = "include" ] && filtered+=("$entry")
    else
      [ "$mode" = "exclude" ] && filtered+=("$entry")
    fi
  done
  DISCOVERED=("${filtered[@]}")
}

if [ "${#ONLY_PATTERNS[@]}" -gt 0 ]; then
  filter_discovered include "${ONLY_PATTERNS[@]}"
fi
if [ "${#EXCLUDE_PATTERNS[@]}" -gt 0 ] && [ "${#DISCOVERED[@]}" -gt 0 ]; then
  filter_discovered exclude "${EXCLUDE_PATTERNS[@]}"
fi

if [ "${#DISCOVERED[@]}" -eq 0 ]; then
  log_warn "No skills matched --only/--exclude selection — nothing to install."
  exit 0
fi

# --- List mode -----------------------------------------------------------------
if [ "$LIST_ONLY" -eq 1 ]; then
  echo "Discovered ${#DISCOVERED[@]} skill(s) in $SOURCE_DIR:"
  echo
  printf '  %-32s  %s\n' "NAME" "PATH"
  printf '  %-32s  %s\n' "----" "----"
  for entry in "${DISCOVERED[@]}"; do
    IFS=$'\t' read -r name path <<<"$entry"
    # Display path relative to REPO_ROOT when possible
    rel="${path#$REPO_ROOT/}"
    printf '  %-32s  %s\n' "$name" "$rel"
  done
  exit 0
fi

# --- Detect duplicate leaf names (e.g. two skills both named "foo") ------------
dup_check() {
  local seen="" name path
  for entry in "${DISCOVERED[@]}"; do
    IFS=$'\t' read -r name path <<<"$entry"
    case " $seen " in
      *" $name "*)
        log_error "Duplicate skill name detected: '$name' — each skill directory must have a unique basename."
        log_error "Conflicting paths include: $path"
        return 1 ;;
    esac
    seen="$seen $name"
  done
}
dup_check || exit 3

# --- Install -------------------------------------------------------------------
log_info "Source : $SOURCE_DIR"
log_info "Target : $TARGET_DIR"
log_info "Mode   : $MODE$( [ "$DRY_RUN" -eq 1 ] && echo ' (dry-run)' )"
log_info "Force  : $( [ "$FORCE" -eq 1 ] && echo yes || echo no )"
log_info "Runtime: $RUNTIME"
log_info "Model  : single-model"
echo

if [ "$DRY_RUN" -eq 0 ]; then
  mkdir -p "$TARGET_DIR"
fi

installed=0
updated=0
skipped=0
failed=0

install_one() {
  local name="$1" src="$2"
  local dst="${TARGET_DIR}/${name}"
  local action=""
  local has_plain=0 has_any_variant=0 selected_file="" materialize_variant=0 variant_context=""
  [ -f "$src/SKILL.md" ] && has_plain=1
  if [ -f "$src/SKILL.claude.md" ] || [ -f "$src/SKILL.openai.md" ]; then
    has_any_variant=1
  fi

  if [ "$RUNTIME" = "codex" ]; then
    variant_context="runtime=codex"
    if [ -f "$src/SKILL.openai.md" ]; then
      selected_file="SKILL.openai.md"
      materialize_variant=1
    elif [ "$has_plain" -eq 1 ]; then
      selected_file="SKILL.md"
    else
      log_error "$name: Codex runtime requires SKILL.openai.md or runtime-neutral SKILL.md"
      return 1
    fi
  else
    variant_context="runtime=claude"
    if [ -f "$src/SKILL.claude.md" ]; then
      selected_file="SKILL.claude.md"
      materialize_variant=1
    elif [ "$has_plain" -eq 1 ]; then
      selected_file="SKILL.md"
    else
      log_error "$name: Claude runtime requires SKILL.claude.md or runtime-neutral SKILL.md"
      return 1
    fi
  fi
  if [ "$selected_file" = "SKILL.md" ] && [ "$has_any_variant" -eq 1 ]; then
    materialize_variant=1
  fi

  if [ -e "$dst" ] || [ -L "$dst" ]; then
    if [ "$FORCE" -eq 0 ]; then
      log_skip "$name (already installed — use --force to overwrite)"
      skipped=$((skipped + 1))
      return 0
    fi
    action="update"
  else
    action="install"
  fi

  if ! audit_codex_skill_tree "$name" "$src" "$selected_file"; then
    return 1
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    if [ "$materialize_variant" -eq 1 ]; then
      log_ok "would $action (copy, $variant_context): $name ← $src ($selected_file -> SKILL.md)"
    elif [ "$MODE" = "link" ]; then
      log_ok "would $action (symlink): $name → $src"
    else
      log_ok "would $action (copy): $name ← $src"
    fi
    [ "$action" = "update" ] && updated=$((updated + 1)) || installed=$((installed + 1))
    return 0
  fi

  # Remove existing target when overwriting.
  if [ "$action" = "update" ]; then
    rm -rf "$dst"
  fi

  if [ "$materialize_variant" -eq 1 ]; then
    # Variant skill: always copy (symlinking would leak variants).
    # Materialize chosen variant as SKILL.md; drop the unused variant(s).
    mkdir -p "$dst"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete \
        --exclude='SKILL.claude.md' --exclude='SKILL.openai.md' \
        $(copy_runtime_aux_excludes) \
        "$src/" "$dst/"
    else
      cp -R "$src/." "$dst/"
      rm -f "$dst/SKILL.claude.md" "$dst/SKILL.openai.md"
      remove_runtime_aux_files "$dst"
    fi
    cp "$src/$selected_file" "$dst/SKILL.md"
    log_ok "$action (copy, $variant_context): $name"
  elif [ "$MODE" = "link" ]; then
    # Use absolute symlink so the target is resilient to cwd changes.
    ln -s "$src" "$dst"
    log_ok "$action (symlink): $name"
  else
    # Prefer rsync if available for robust copy semantics; fall back to cp.
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete $(copy_runtime_aux_excludes) "$src/" "$dst/"
    else
      cp -R "$src" "$dst"
      remove_runtime_aux_files "$dst"
    fi
    log_ok "$action (copy): $name"
  fi
  [ "$action" = "update" ] && updated=$((updated + 1)) || installed=$((installed + 1))
}

for entry in "${DISCOVERED[@]}"; do
  IFS=$'\t' read -r name path <<<"$entry"
  if ! install_one "$name" "$path"; then
    log_error "Failed to install: $name"
    failed=$((failed + 1))
  fi
done

echo
log_info "Summary: installed=${installed}  updated=${updated}  skipped=${skipped}  failed=${failed}"

if [ "$failed" -gt 0 ]; then
  exit 3
fi
exit 0
