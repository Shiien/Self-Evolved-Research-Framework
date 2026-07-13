#!/usr/bin/env bash
# Deterministic LaTeX build pipeline, migrated from the paper-compile skill.
# Pre-compile integrity checks -> pdflatex x3 + bibtex/biber -> error summary
# -> PDF to outputs/paper/. The paper-assets skill (COMPILE mode) drives this
# and handles the judgment (choosing among multiple mains, confirming fixes).
#
# Usage: scripts/compile_paper.sh [MAIN.tex] [--keep-aux] [--shell-escape]
# Exit codes: 0 ok | 1 compile error | 2 pre-check failed | 3 no main found
set -u
cd "$(dirname "$0")/.." || exit 3

PAPER_DIR="paper/papers"
OUT_DIR="outputs/paper"
KEEP_AUX=0
SHELL_ESCAPE=""
MAIN=""

for arg in "$@"; do
  case "$arg" in
    --keep-aux) KEEP_AUX=1 ;;
    --shell-escape) SHELL_ESCAPE="-shell-escape" ;;
    *.tex) MAIN="$arg" ;;
  esac
done

# --- 1. locate main ----------------------------------------------------------
if [ -z "$MAIN" ]; then
  for cand in main.tex paper.tex; do
    [ -f "$PAPER_DIR/$cand" ] && MAIN="$PAPER_DIR/$cand" && break
  done
  if [ -z "$MAIN" ]; then
    mapfile -t texes < <(find "$PAPER_DIR" -maxdepth 1 -name '*.tex' 2>/dev/null)
    if [ "${#texes[@]}" -eq 1 ]; then
      MAIN="${texes[0]}"
    else
      echo "[compile] no unambiguous main .tex under $PAPER_DIR (found ${#texes[@]})."
      echo "          Pass it explicitly: scripts/compile_paper.sh $PAPER_DIR/<file>.tex"
      exit 3
    fi
  fi
fi
[ -f "$MAIN" ] || { echo "[compile] $MAIN not found"; exit 3; }
MAIN_DIR="$(dirname "$MAIN")"
MAIN_BASE="$(basename "$MAIN" .tex)"
echo "[compile] main: $MAIN"

# --- 2. pre-compile integrity checks ------------------------------------------
# Collect refs from the main file and one level of \input (comments stripped).
collect() { sed 's/%.*//' "$1" 2>/dev/null | grep -oE '\\(input|include|includegraphics(\[[^]]*\])?|bibliography|addbibresource)\{[^}]+\}'; }
refs="$(collect "$MAIN")"
while IFS= read -r inc; do
  refs+=$'\n'"$(collect "$MAIN_DIR/${inc}.tex")"
done < <(printf '%s\n' "$refs" | grep -oE '\\(input|include)\{[^}]+\}' | sed -E 's/.*\{([^}]+)\}/\1/' | sed 's/\.tex$//')

fail=0
while IFS= read -r r; do
  [ -z "$r" ] && continue
  target="$(printf '%s' "$r" | sed -E 's/.*\{([^}]+)\}/\1/')"
  case "$r" in
    \\input*|\\include\{*)
      f="$MAIN_DIR/${target%.tex}.tex"
      [ -f "$f" ] || { echo "  MISSING input: $f"; fail=1; } ;;
    \\includegraphics*)
      found=0
      for ext in "" .pdf .png .jpg .jpeg .svg .tex; do
        for base in "$MAIN_DIR" "paper/figures" "."; do
          [ -f "$base/${target}${ext}" ] && found=1 && break 2
        done
      done
      [ "$found" -eq 1 ] || { echo "  MISSING figure: ${target}"; fail=1; } ;;
    \\bibliography*|\\addbibresource*)
      f="$MAIN_DIR/${target%.bib}.bib"
      { [ -f "$f" ] && [ -s "$f" ]; } || { echo "  MISSING/empty bib: $f"; fail=1; } ;;
  esac
done < <(printf '%s\n' "$refs")

if [ "$fail" -eq 1 ]; then
  echo "[compile] pre-compile check: FAIL — fix the missing targets, then re-run."
  exit 2
fi
echo "[compile] pre-compile check: ok"

# --- 3. bibliography tool ------------------------------------------------------
BIBTOOL=""
if grep -q '\\addbibresource' "$MAIN" && command -v biber >/dev/null 2>&1; then
  BIBTOOL="biber"
elif grep -qE '\\bibliography\{' "$MAIN"; then
  BIBTOOL="bibtex"
fi

# --- 4. pipeline ----------------------------------------------------------------
LOG="$(mktemp /tmp/compile_paper.XXXXXX.log)"
run_pass() {
  ( cd "$MAIN_DIR" && "$@" ) >>"$LOG" 2>&1
}
ok=1
run_pass pdflatex -interaction=nonstopmode -halt-on-error $SHELL_ESCAPE "$MAIN_BASE.tex" || ok=0
if [ "$ok" -eq 1 ] && [ -n "$BIBTOOL" ]; then
  run_pass "$BIBTOOL" "$MAIN_BASE" || echo "[compile] warn: $BIBTOOL exited non-zero (see log)"
fi
if [ "$ok" -eq 1 ]; then
  run_pass pdflatex -interaction=nonstopmode -halt-on-error $SHELL_ESCAPE "$MAIN_BASE.tex" || ok=0
fi
if [ "$ok" -eq 1 ]; then
  run_pass pdflatex -interaction=nonstopmode -halt-on-error $SHELL_ESCAPE "$MAIN_BASE.tex" || ok=0
fi

# --- 5. summary -------------------------------------------------------------------
echo "[compile] --- issue summary ---"
grep -E '^! ' "$LOG" | sort -u | head -10 | sed 's/^/  ERROR /'
grep -E "LaTeX Error: File .*\.sty' not found" "$LOG" | sort -u | head -5 | sed 's/^/  MISSING-PACKAGE /'
grep -E 'Warning: Citation .* undefined' "$LOG" | sed -E "s/.*Citation .([^']+).*/  UNDEF-CITATION \1/" | sort -u | head -20
grep -E 'Warning: Reference .* undefined' "$LOG" | sed -E "s/.*Reference .([^']+).*/  UNDEF-REFERENCE \1/" | sort -u | head -20
grep -cE 'Overfull \\hbox' "$LOG" | sed 's/^/  overfull-hboxes: /'

if [ "$ok" -eq 0 ]; then
  echo "[compile] FAILED — full log: $LOG (aux files kept for debugging)"
  exit 1
fi

# --- 6. save PDF + cleanup ----------------------------------------------------------
mkdir -p "$OUT_DIR"
cp "$MAIN_DIR/$MAIN_BASE.pdf" "$OUT_DIR/$MAIN_BASE.pdf"
pages=""
command -v pdfinfo >/dev/null 2>&1 && pages=" $(pdfinfo "$OUT_DIR/$MAIN_BASE.pdf" 2>/dev/null | awk '/^Pages:/{print $2 " pages,"}')"
echo "[compile] OK -> $OUT_DIR/$MAIN_BASE.pdf (${pages} $(du -h "$OUT_DIR/$MAIN_BASE.pdf" | cut -f1))"
if [ "$KEEP_AUX" -eq 0 ]; then
  ( cd "$MAIN_DIR" && rm -f "$MAIN_BASE".{aux,log,out,toc,bbl,blg,run.xml,bcf} )
fi
rm -f "$LOG"
exit 0
