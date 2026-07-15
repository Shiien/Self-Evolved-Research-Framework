---
name: paper-assets
description: >-
  All paper production tooling in one mode-based skill — ILLUSTRATE (rigorous
  structural diagrams: architecture / pipeline / flow / concept map, TikZ or
  SVG), FIGURE (data-driven plots from experiment results with the generation
  script preserved for reproducibility), ART (decorative identity visuals:
  pixel art, mascots, README heroes), COMPILE (build the paper PDF via
  scripts/compile_paper.sh with integrity pre-checks and confirmed auto-fixes).
  Absorbs the former paper-illustrate / paper-figure / paper-art / paper-compile
  skills — those names now refer to modes here. Triggers on "draw the
  architecture", "画架构图", "plot the results", "bar chart", "heatmap", "画图",
  "pixel art", "project mascot", "compile the paper", "build PDF", "编译论文".
---

# paper-assets

Mode routing: structural diagram (no data) → ILLUSTRATE · plot of numbers →
FIGURE · decorative/identity → ART · build PDF → COMPILE.

## Mode: ILLUSTRATE — "draw the architecture / pipeline / flow"

1. Anchor terminology: `methodology/approach.md`; match notation to the
   relevant `paper/papers/{section}.tex` if the figure serves one.
2. Pick type and format: architecture / pipeline / flow chart / concept map
   / A-vs-B comparison; **TikZ** for conference papers, **SVG** for slides,
   README, internal docs. Horizontal left→right flow for papers unless
   hierarchy demands vertical.
3. Academic conventions: consistent node/arrow vocabulary (one shape per
   component class), notation identical to the paper, no decorative color —
   grayscale-safe with ≤1 accent, label every arrow that carries data,
   caption-sized (readable at column width).
4. Save: TikZ → `paper/figures/{name}.tex` (standalone-compilable); SVG →
   `paper/figures/{name}.svg`. Iterate with the user on layout before
   polishing details.

## Mode: FIGURE — "plot the results", after `experiment-analyze`

1. Locate the data: `runs/<id>/` metrics/eval, `experiments/`,
   `logs/experiments/`, or user-supplied. Never type numbers in by hand —
   the script reads the source file.
2. Pick type (line = trends, bar = categorical comparison, scatter =
   correlation, heatmap = 2D sweeps, table = exact values) and backend
   (matplotlib/seaborn for iteration; PGFPlots for camera-ready).
3. **The script is the artifact**: save `paper/figures/scripts/{name}.py`
   (or `.tex`), reading data from its source path, deterministic, emitting
   both `paper/figures/{name}.pdf` and `.png`. Reviewers must be able to
   reproduce the figure by running it.
4. Conventions: error bars/bands whenever seeds > 1 (state n in caption),
   axis labels with units, colorblind-safe palette, no chartjunk; legend
   outside the axes if it occludes data.
5. Run the script, confirm outputs land; re-tag the script in git before
   regenerating a figure the paper already cites.

## Mode: ART — "pixel art", "mascot", "README hero"

1. Context: `config.yaml` (domain, brand color), prior visuals in
   `outputs/visuals/` for palette consistency.
2. Design flat SVG / pixel-grid art; keep one palette across paper, README
   and slides; no text baked into the image unless asked.
3. Save `outputs/visuals/{name}.svg`; if the visual is a tracked
   deliverable → `checklist` (update mode).

## Mode: COMPILE — "build the PDF", "编译论文"

Explicit build requests only — not every section edit.
1. Run the deterministic pipeline:
   ```bash
   bash scripts/compile_paper.sh [paper/papers/<main>.tex] [--shell-escape]
   ```
   It does: main-file resolution, pre-compile integrity checks (`\input` /
   `\includegraphics` / bib targets must resolve — fails BEFORE burning
   three passes), bibtex-vs-biber detection, pdflatex×3 + bib pass, a
   compact issue summary (errors with file:line, missing packages,
   undefined citations/references, overfull count), PDF →
   `outputs/paper/`, aux cleanup on success (kept on failure).
2. Judgment stays here:
   - multiple candidate mains → ask, never guess;
   - missing `\usepackage` / single-char encoding fixes → propose the
     patch, apply only on user confirmation, re-run;
   - undefined citations → never fabricate; point at
     `scripts/citation_fetch.py` (see `writing` draft mode);
   - preamble changed → delete stale `.aux`/`.bbl` before re-running;
   - `\write18`/shell-escape errors → retry once with `--shell-escape`
     and note the CI requirement;
   - exit 0 with UNDEF-CITATION lines still means `[?]` in the PDF —
     surface them.

**Inputs**: concept/data/main-tex per mode
**Outputs**: `paper/figures/` (tex/svg/pdf/png + scripts/), `outputs/visuals/`,
`outputs/paper/{name}.pdf`
**Token**: ILLUSTRATE 3-8K · FIGURE 3-8K · ART 2-5K · COMPILE 1-3K (the build is shell)
**Composition**: FIGURE chains from `experiment-analyze`; finished figures →
`writing` (draft mode) for the prose that cites them; clean pre-submission
build → `writing-review`.
