# peer-review — venue-aware AI peer review pipeline

Extension of the multi-stage AI peer review system in
[**AI-Assisted Peer Review at Scale: AAAI-26 Pilot** (arxiv 2604.13940)](https://arxiv.org/abs/2604.13940),
decomposed into composable agent skills and extended with:

- **Venue level selection**: `poster` / `oral` / `best_paper`, with oral and best-paper requiring explicit evidence of new insight and strong method.
- **Interactive launch**: the orchestrator asks the user for level / reviewer count / reviewer backgrounds / recommendation-on-off before it touches the paper, and lets the user edit the level-specific bar text per run.
- **Multi-reviewer mode**: optionally spawn 2–3 parallel reviewer sub-agents (each with its own background), then run an SAC (Senior Area Chair) meta-summary pass.
- **Recommendation**: emit one of `accept` / `weak accept` / `weak reject` / `reject` (default ON, can be disabled).

## Skills in this family

| Skill | Role |
|---|---|
| `peer-review` | Orchestrator. Collects run config, preprocesses, dispatches stages or reviewer sub-agents, writes outputs. |
| `peer-review-story` | Stage 1 — narrative / gap-claim audit (no tools). |
| `peer-review-presentation` | Stage 2 — clarity, headings, notation (no tools). |
| `peer-review-evaluations` | Stage 3 — baselines, metrics, stats; uses Bash code interpreter. |
| `peer-review-correctness` | Stage 4 — equations, proofs, algorithms; uses Bash. |
| `peer-review-significance` | Stage 5 — novelty + citation verification; uses WebSearch/WebFetch. |
| `peer-review-critique` | Stage 6 — compile → self-critique → revise into AAAI format; emits optional recommendation. |
| `peer-review-qa` | Stage 7 — bias, offensive language, citation hallucination spot check. |
| `peer-review-sac` | Multi-reviewer only — meta-summarize N reviews into `sac_summary.md` with unified recommendation. |

Preprocessing (PDF → markdown) delegates to `document-skills:pdf`.

## Usage

Trigger the orchestrator with any of:
- "Review this paper: `<arxiv URL>`"
- "Peer-review `paper/draft.pdf`"
- "Generate a reviewer report for `<path>`"
- "Run a 3-reviewer best-paper-level review of `<path>`"

The orchestrator will:
1. Ask for the venue level and show/edit the level-specific bar.
2. Ask for reviewer count and (if >1) each reviewer's background.
3. Ask whether to emit an accept/reject recommendation (default yes).
4. Preprocess the paper once.
5. Dispatch stages (solo) or parallel reviewer sub-agents + SAC (multi).
6. Write outputs under `outputs/peer-review/<paper_id>/`.

Skip the prompts with inline overrides, e.g. `peer-review <url> level=oral reviewers=3 rec=yes`.

## Shared assets (all under `peer-review/shared/`)

- `base_instruction.md` — reviewer objectives, factual standards, PDF/markdown complementarity, level-bar handling, multi-reviewer persona handling.
- `review_level.yaml` — per-level bar text + recommendation thresholds (`poster` / `oral` / `best_paper`).
- `review_schema.md` — YAML frontmatter + required sections for every stage's findings file.
- `output_format.md` — AAAI review format (6 mandatory sections + 1 optional Recommendation section, 400–1500 words).
- `rubric.yaml` — per-stage `must_check` lists.

Per-run assets (written by orchestrator into `outputs/peer-review/<paper_id>/`):
- `run_config.yaml` — chosen level, reviewer count, reviewer backgrounds, recommendation flag.
- `level_bar.md` — the (possibly user-edited) level bar text actually appended to stages this run.

## Testing

```bash
SER_SKILLS_ROOT=/path/to/skills bash /path/to/skills/peer-review/tests/run_all_tests.sh
```

Four hermetic test layers (no LLM calls, <2s):

| Layer | Purpose |
|---|---|
| 1. Static lint | All SKILL.md files (including `peer-review-sac`) have valid frontmatter; orchestrator references every stage + SAC; shared assets (including `review_level.yaml`) exist and parse; rubric covers all stages. |
| 2. Negative cases | Schema and output-format validators correctly REJECT malformed inputs. |
| 3. Stage findings | Golden fixture findings for each stage pass schema and contain the expected `[severity]` flag for a seeded flaw in the toy paper. |
| 4. E2E pipeline | All stage outputs schema-valid; final review has all 6 AAAI sections (and optionally a valid Recommendation section); QA flags the seeded fabricated citation; Weaknesses list reflects fingerprints from every earlier stage. |

## Architecture notes

The paper's five review dimensions (Story, Presentation, Evaluations, Correctness, Significance) map 1:1 to the five stage skills. The paper's compile → self-critique → revise loop is merged into `peer-review-critique` (one skill, three sub-steps). QA is a separate skill (`peer-review-qa`). Each stage receives all previous stage outputs to match the paper's feed-forward design.

**New in this version:**
- A per-run `level_bar.md` is appended to `base_instruction.md` when the orchestrator dispatches any stage — this flows the venue's strictness into every stage, not just the final recommendation.
- Multi-reviewer mode spawns N reviewer sub-agents in parallel (one dispatch message, N `Agent` tool calls). Each runs stages 01–06 in its own subdir. QA runs per reviewer; SAC summarizes across reviewers.
- `peer-review-sac` deliberately produces a SHORT meta-summary with only 4 sections (Reviewers, Points of consensus, Points of disagreement, Unified Recommendation), **not** an AAAI-format review. The individual reviewer `06_final.md` files remain the primary deliverables.
