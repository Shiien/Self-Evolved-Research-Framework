#!/usr/bin/env bash
# install-skills.sh — Install bundled Claude Code skills into a .claude/skills directory
#
# Auto-discovers every directory containing a SKILL.md under the source tree
# (default: ./skills), and installs each one into a target skills directory
# (default: ./.claude/skills) as either a copy or a symlink.
#
# Directories without a SKILL.md (e.g. skills/_shared, skills/td-nl) are ignored:
# they are SER internal infrastructure, not Claude Code skills.
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
#   -l, --link            Symlink instead of copying (ideal for development)
#   -s, --source DIR      Source directory to scan (default: ./skills)
#   -t, --target DIR      Target directory            (default: ./.claude/skills)
#       --user            Shortcut for --target ~/.claude/skills (global install)
#       --only PATTERNS   Install only skills matching PATTERNS (comma-separated,
#                         glob supported; e.g. 'paper-*,code-*').
#                         Repeatable; union of all patterns is kept.
#       --exclude PATTERNS  Skip skills matching PATTERNS (comma-separated, glob
#                         supported; e.g. 'proof-*,theory-generalize'). Applied
#                         after --only. Repeatable; union of all patterns.
#       --codex-track T   Select codex-augmented variants: 'claude' (default) or 'codex'.
#                         'claude' installs the upstream, Claude-only variant of every
#                         skill that ships a codex variant — no external deps required.
#                         'codex' installs the Codex-augmented variant where the skill
#                         adds an extra Codex pass (code-implement: /codex:rescue for
#                         medium/large; code-review: /codex:review second reviewer;
#                         writing-review: 3rd Codex peer reviewer; idea-verify: 4th
#                         evidence source via `mcp__codex__codex`).
#                         For skills that ship track variants (code-implement, code-review,
#                         writing-review, idea-verify), the matching SKILL.T.md is
#                         materialized as SKILL.md. 'codex' strictly preflights codex
#                         deps (/codex:setup, Superpowers, /codex:review, mcp__codex__codex).
#       --list            List discovered skills (after --only/--exclude filters)
#                         and exit without installing
#       --no-color        Disable ANSI color output
#
# Selection examples:
#   --only 'paper-*'                       # all paper-* skills
#   --only paper-read,writing-draft        # pick two skills
#   --exclude 'theory-*,proof-*'           # drop theory + proof families
#   --only 'paper-*' --exclude paper-index # paper-* minus paper-index
#   --codex-track codex                    # install Codex-augmented variants for every
#                                          # skill that ships them (code + research family)
#   --only 'code-*' --codex-track claude   # install only code family, upstream Claude-only variants
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
TARGET_DIR="${REPO_ROOT}/.claude/skills"
MODE="copy"          # copy | link
DRY_RUN=0
FORCE=0
LIST_ONLY=0
USE_COLOR=1
ONLY_PATTERNS=()
EXCLUDE_PATTERNS=()
CODEX_TRACK="claude"    # claude | codex — selects SKILL.{track}.md variant for any skill that ships variants

# --- Helpers -------------------------------------------------------------------
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
                    TARGET_DIR="$2"; shift 2 ;;
    --user)         TARGET_DIR="${HOME}/.claude/skills"; shift ;;
    --only)         [ $# -ge 2 ] || { log_error "--only requires an argument"; exit 1; }
                    IFS=',' read -r -a _tmp <<<"$2"
                    ONLY_PATTERNS+=("${_tmp[@]}")
                    shift 2 ;;
    --exclude)      [ $# -ge 2 ] || { log_error "--exclude requires an argument"; exit 1; }
                    IFS=',' read -r -a _tmp <<<"$2"
                    EXCLUDE_PATTERNS+=("${_tmp[@]}")
                    shift 2 ;;
    --codex-track)  [ $# -ge 2 ] || { log_error "--codex-track requires an argument"; exit 1; }
                    case "$2" in
                      claude|codex) CODEX_TRACK="$2" ;;
                      *) log_error "--codex-track must be 'claude' or 'codex' (got: $2)"; exit 1 ;;
                    esac
                    shift 2 ;;
    --list)         LIST_ONLY=1; shift ;;
    --no-color)     USE_COLOR=0; shift ;;
    --)             shift; break ;;
    -*)             log_error "Unknown option: $1"; usage 1 ;;
    *)              log_error "Unexpected argument: $1"; usage 1 ;;
  esac
done

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

# --- Codex preflight (only runs when --codex-track codex) ---------------------
# Track B (codex) strictly requires:
#   1. `codex login status` reports an authenticated session (non-interactive
#      check — `/codex:setup` cannot be used here because it opens a TUI and
#      fails in non-TTY shells).
#   2. `/codex:review` skill available (used by code-review Track B).
#   3. `mcp__codex__codex` MCP server reachable (used by writing-review and
#      idea-verify Track B for cross-model review).
#
# NOTE: Superpowers is NOT preflighted here. Superpowers is a Codex-side plugin
# (installed inside Codex itself, not in Claude Code's skill tree), so there is
# no reliable way to probe it from this Claude-side installer. It is strongly
# recommended for best results on the Codex track — see README for the install
# link.
#
# Any failure aborts installation with a clear remediation message.
preflight_codex() {
  local problems=0

  log_info "Codex track preflight — checking dependencies…"

  # 1. Codex CLI + authenticated login.
  # We use `codex login status` instead of `codex /codex:setup` because the
  # latter launches an interactive TUI that fails in non-TTY shells with
  # "stdin is not a terminal". `codex login status` is a non-interactive
  # subcommand that prints the current login state and exits with 0 when
  # authenticated.
  if ! command -v codex >/dev/null 2>&1; then
    log_error "codex CLI not found on PATH. Install Codex before using --codex-track codex."
    problems=$((problems + 1))
  else
    local login_out=""
    if ! login_out="$(codex login status 2>&1)" || ! printf '%s' "$login_out" | grep -qiE 'logged in|authenticated'; then
      log_error "Codex CLI is not logged in. Run \`codex login\` (ChatGPT or API key) and retry."
      problems=$((problems + 1))
    fi
  fi

  # 2. /codex:review availability
  if ! command -v codex >/dev/null 2>&1; then
    : # already reported above
  elif ! codex /codex:review --help >/dev/null 2>&1 && ! codex help 2>/dev/null | grep -q 'codex:review'; then
    log_error "/codex:review skill not available. Install it before using --codex-track codex."
    problems=$((problems + 1))
  fi

  # 3. mcp__codex__codex MCP server — best-effort probe via `claude mcp`.
  # We skip hard failure if claude CLI isn't available (Codex CLI alone is
  # enough for /codex:* skills). When `claude mcp` is present, list servers
  # and look for the codex entry.
  if command -v claude >/dev/null 2>&1; then
    local mcp_list=""
    if mcp_list="$(claude mcp list 2>/dev/null)"; then
      if ! printf '%s' "$mcp_list" | grep -qiE 'codex'; then
        log_error "mcp__codex__codex MCP server not registered. Run \`claude mcp add codex <command>\` or equivalent before using --codex-track codex."
        problems=$((problems + 1))
      fi
    else
      log_warn "Could not query \`claude mcp list\` — skipping mcp__codex__codex preflight. Ensure it is registered for writing-review / idea-verify cross-model reviews."
    fi
  else
    log_warn "claude CLI not on PATH — skipping mcp__codex__codex preflight. Ensure it is registered for writing-review / idea-verify cross-model reviews."
  fi

  if [ "$problems" -gt 0 ]; then
    log_error "Codex preflight failed with $problems issue(s). Fix the above or rerun with --codex-track claude."
    exit 1
  fi
  log_ok "Codex preflight passed."
}

if [ "$CODEX_TRACK" = "codex" ] && [ "$LIST_ONLY" -eq 0 ] && [ "$DRY_RUN" -eq 0 ]; then
  preflight_codex
fi

# --- Discovery -----------------------------------------------------------------
# Find every directory that contains a SKILL.md OR a track-variant
# (SKILL.claude.md / SKILL.codex.md). Store (name, abs_path) pairs.
# "name" is the leaf directory name — Claude Code indexes skills by that.
#
# For directories containing ONLY track variants (no plain SKILL.md), the
# directory is a track-variant skill: install_one will materialize the chosen
# variant as SKILL.md at the target.
#
# We deliberately use `-print0` + null-delim read to be safe with unusual names.
discover_skills() {
  local roots=()
  # Match SKILL.md, SKILL.claude.md, SKILL.codex.md — then dedupe by directory.
  while IFS= read -r -d '' f; do
    roots+=("$f")
  done < <(find "$SOURCE_DIR" -type f \
            \( -name 'SKILL.md' -o -name 'SKILL.claude.md' -o -name 'SKILL.codex.md' \) \
            -print0 | sort -z)

  # Dedupe by directory — a single dir may contain both SKILL.claude.md and
  # SKILL.codex.md, but it is still one skill.
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
log_info "Codex  : track=$CODEX_TRACK"
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
  # Track-variant detection: does the source dir have SKILL.{track}.md variants
  # but no plain SKILL.md? (a plain SKILL.md means the skill has no track split
  # and should be installed as-is.)
  local has_plain=0 has_variant=0 variant_file=""
  [ -f "$src/SKILL.md" ] && has_plain=1
  if [ -f "$src/SKILL.${CODEX_TRACK}.md" ]; then
    has_variant=1
    variant_file="SKILL.${CODEX_TRACK}.md"
  fi
  # If variant files exist but the selected track's variant is missing, warn
  # and fall back to whichever variant is present (preferring claude).
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

  if [ "$DRY_RUN" -eq 1 ]; then
    if [ "$has_variant" -eq 1 ] && [ "$has_plain" -eq 0 ]; then
      log_ok "would $action (copy, track=$CODEX_TRACK): $name ← $src ($variant_file → SKILL.md)"
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

  if [ "$has_variant" -eq 1 ] && [ "$has_plain" -eq 0 ]; then
    # Track-variant skill: always copy (symlinking would leak both variants).
    # Materialize chosen variant as SKILL.md; drop the unused variant(s).
    mkdir -p "$dst"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete \
        --exclude='SKILL.claude.md' --exclude='SKILL.codex.md' \
        "$src/" "$dst/"
    else
      cp -R "$src/." "$dst/"
      rm -f "$dst/SKILL.claude.md" "$dst/SKILL.codex.md"
    fi
    cp "$src/$variant_file" "$dst/SKILL.md"
    log_ok "$action (copy, track=$CODEX_TRACK): $name"
  elif [ "$MODE" = "link" ]; then
    # Use absolute symlink so the target is resilient to cwd changes.
    ln -s "$src" "$dst"
    log_ok "$action (symlink): $name"
  else
    # Prefer rsync if available for robust copy semantics; fall back to cp.
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete "$src/" "$dst/"
    else
      cp -R "$src" "$dst"
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
