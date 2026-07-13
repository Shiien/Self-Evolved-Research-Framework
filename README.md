# SER — Self-Evolved Research

> A behavior-driven research framework for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).
> Skills trigger automatically. The framework improves its own skills through use.
>
> **[中文版 README](README.zh-CN.md)**

<p align="center">
  <img src="ser_architecture_overview.svg" alt="SER Architecture Overview" width="700"/>
</p>

## What It Does

You talk naturally. SER detects your intent and routes to the right micro-skill:

| You say | SER triggers |
|---------|-------------|
| "I'm reading this paper..." | `paper-read` — structured notes |
| "Search arXiv for X" | `paper-lit-search` — arXiv + Semantic Scholar |
| "Is this proof correct?" | `proof` (critique mode) — step-by-step check |
| "Prove that …" | `proof` (write mode) — first draft of the proof |
| "What should I do next?" | `plan-suggest` — prioritized tasks |
| "Design the experiment" | `experiment-plan` — claims / variables / baselines |
| "Sweep these hyperparameters" | `experiment-dse` — search strategy + configs |
| "Run the experiment" | `experiment-run` — contract-gated launch via `harness ext-launch` |
| "Any novel ideas for X?" | `idea` (discover) → `idea-verify` → `idea` (refine) |
| "Write the introduction" | `writing` (draft mode) — section draft |
| "Plot the results as a bar chart" | `paper-assets` (figure mode) — PGFPlots / matplotlib |
| "Compile the paper" | `paper-assets` (compile mode) — `scripts/compile_paper.sh` |
| "Implement this feature" | `code` (roadmap) → `code-implement` → `code-review` → `code` (commit) |
| (end conversation) | `session-close` — evidence-first wrap-up |

Every skill execution generates feedback. Over sessions, SER proposes improvements
to its own skill specs via natural language TD learning — the skills you use today
become better tomorrow.

## Getting Started

### 1. Clone

```bash
git clone --recurse-submodules https://github.com/Shiien/Self-Evolved-Research-Framework.git
cd Self-Evolved-Research-Framework
```

> **Already cloned without `--recurse-submodules`?** Run:
> ```bash
> git submodule update --init --recursive
> ```

### 2. Run Setup

```bash
bash scripts/setup.sh
```

This creates `config.yaml`, initializes the memory system, and sets up all required directories. Safe to run multiple times.

### 3. Configure Your Project

Edit `config.yaml` with your project details:

```yaml
project:
  name: "Your Research Project"
  status: "phase-0-exploration"
  created_at: "2026-03-19"

research:
  domain: "Your Domain"
  sub_domain: "Your Sub-Domain"
  keywords: [...]
```

### 4. Start Working

```bash
claude
```

SER will automatically:
1. Inject deterministic session context via the `SessionStart` hook (`scripts/session_context.sh`)
2. Show a status banner (`session-open`) — research question, experiment ledger, last run
3. Wait for your research request — no commands needed

### 5. Install the skills into `.claude/skills/`

```bash
bash scripts/install-skills.sh            # copy into ./.claude/skills
bash scripts/install-skills.sh --link     # symlink (dev workflow)
bash scripts/install-skills.sh --user     # install into ~/.claude/skills
bash scripts/install-skills.sh --list     # list discovered skills
bash scripts/install-skills.sh --dry-run  # preview without writing
bash scripts/install-skills.sh --force    # overwrite existing skills
```

**Selective install** — pick or drop skill families:

```bash
bash scripts/install-skills.sh --only 'paper-*'
bash scripts/install-skills.sh --only 'code*,paper-assets'
bash scripts/install-skills.sh --exclude 'theory,proof'
```

**Codex track** — for skills that ship a Codex-augmented variant
(`code-implement`, `code-review`, `writing-review`, `idea-verify`):

```bash
bash scripts/install-skills.sh --codex-track claude   # default, upstream Claude-only
bash scripts/install-skills.sh --codex-track codex    # Codex-augmented cross-model review
```

The `codex` track adds an extra Codex pass:
`code-implement` dispatches `/codex:rescue` for medium/large tasks;
`code-review` adds `/codex:review` as a second reviewer;
`writing-review` adds a 3rd Codex peer reviewer;
`idea-verify` adds a 4th evidence source via `mcp__codex__codex`.
When selected, the installer strictly preflights Codex CLI + Superpowers +
`/codex:review` + `mcp__codex__codex` and aborts if any dep is missing.

Each SER skill lives in its own directory under `skills/` with a standard
`SKILL.md` (YAML frontmatter + body), so Claude Code auto-discovers and
auto-triggers them once installed.

## Skills (27 SER + 1 external — consolidated from 57, see REFACTOR_PLAN.md §7)

Each skill lives in `skills/{skill-name}/SKILL.md` with standard YAML frontmatter.
Skills marked † ship both `SKILL.claude.md` and `SKILL.codex.md` variants — pick
via `--codex-track` at install time.

| Category | Skills | Purpose |
|----------|--------|---------|
| **Session** | `session-open`, `session-close` | Lifecycle: status banner, auto-save |
| **Paper reading** | `paper-read` (standard / deep / compare / index modes), `paper-lit-search` | Reading, comparison, arXiv + Semantic Scholar search |
| **Paper writing** | `writing` (outline / draft / polish modes), `writing-review`† | Outline → draft → peer-review → polish |
| **Paper build** | `paper-assets` (illustrate / figure / art / compile modes) | Architecture diagrams, data plots, pixel art, LaTeX build (`scripts/compile_paper.sh`) |
| **Theory** | `theory` (formalize / decompose / search / counterexample / generalize modes) | Formalization & proof strategy |
| **Proof** | `proof` (write / critique / fix / formalize / verify modes) | First draft → review → repair → publication LaTeX → spot-check |
| **Ideas** | `idea` (explore / discover / refine modes), `idea-verify`† | Directions → gap analysis → novelty check → sharpened proposal |
| **Experiment** | `experiment-plan`, `experiment-dse`, `experiment-run`, `experiment-monitor` (thin, over `harness ext-status`), `experiment-analyze` | Contract → sweep → dispatch → monitor → evaluate |
| **Coding** | `code` (branch / roadmap / debug / commit modes), `code-implement`†, `code-review`† | Plan → branch → implement → debug → review → commit |
| **Planning** | `plan-suggest` (+milestone mode), `decision-analyze` (+converge mode) | Project management (status → `python -m harness status`; progress reports → `checklist`) |
| **Checklist** | `checklist` (modes: create / update / verify / recount) | Paper audit & claim tracking |
| **Memory** | `memory` (modes: write / retrieve / consolidate / forget) | Persistent cross-session memory |
| **Meta** | `skill-feedback`, `evolve-suggest`, `evolve-apply` | TD-NL skill self-improvement |
| **Integration** | `project-integrate` | Merge SER into an existing project |

## External Skills

| Skill | Source | Purpose |
|-------|--------|---------|
| [Fey-R](https://github.com/xvirobotics/fey-r) | `skills/external/fey-r/` | Interactive Feynman-method paper reading — deeply understand papers by recreating the author's derivation |

External skills are installed as git submodules and initialized automatically by `scripts/setup.sh`.
To add your own, use `git submodule add <url> skills/external/<name>/`.

## Skill Evolution (TD-NL)

The framework optimizes its own micro-skill specs through natural language TD learning:

```
skill fires → G2 assessment (was it useful?) → accumulate over sessions
                                                        ↓
session.close → G1 aggregation → per-skill value update → spec edit proposal
                                                        ↓
                                    user approves → evolve.apply → rollback if quality drops
```

The optimization target is the skill specs themselves (`skills/{skill-name}/SKILL.md`).
Version history in `skills/td-nl/history/` enables safe rollback.

## Research Harness

Experiments (currently the TTT skill-evolution experiment) run through one
canonical, contract-gated path — see `REFACTOR_PLAN.md` for design and
`RESEARCH_STATE.md` / `EXPERIMENTS.json` for live research state:

```bash
python -m harness setup                          # environment check
python -m harness smoke-test                     # full deterministic test suite
python -m harness run configs/ttt_smoke.yaml     # one experiment -> runs/<id>/
python -m harness evaluate <run>                 # (re-)evaluate vs the contract
python -m harness resume <run>                   # finish a failed/partial run
python -m harness compare <run> <run> ...        # metric/verdict table
python -m harness loop step                      # run the next planned experiment
```

Every run directory is self-contained (resolved config, contract + hash, seed
and git metadata, logs, metrics, checkpoints, evaluation, failure info,
summary). An experiment is complete only after its evaluation has run.

## Project Structure

```
├── CLAUDE.md              # Research protocol (loop, state model, intent router)
├── RESEARCH_STATE.md      # Scientific state: question, hypotheses, evidence
├── EXPERIMENTS.json       # Experiment ledger (planned/running/complete + verdicts)
├── harness/               # Minimal research harness (contract, rundir, cli, loop)
├── configs/               # Experiment configs, each with a pre-registered contract
├── runs/                  # Self-contained run records
├── tests/                 # Harness + regression tests (baseline check)
├── config.template.yaml   # Copy to config.yaml and customize
├── README.md / LICENSE
├── skills/
│   ├── {skill-name}/      # 27 SER skills (consolidated from 57; mode-based)
│   ├── _shared/           # Shared infra read by related skills
│   │   ├── checklist-engine.md
│   │   ├── memory-tiers.md
│   │   ├── evolve-cycle.md
│   │   ├── codex-contract.md       # Codex track behaviour contract
│   │   ├── cross-model-review.md   # ADD-mode cross-model review protocol
│   │   └── git-conventions.md      # Shared git workflow
│   ├── external/          # External skills (git submodules)
│   │   └── fey-r/         # Feynman-method paper reading
│   └── td-nl/             # Skill evolution infrastructure
│       ├── feedback-log.md
│       ├── value-function.md
│       ├── skill-values/   # Per-skill Q^L estimates
│       └── history/        # Spec version archive for rollback
├── scripts/               # session_context.sh (SessionStart hook), citation, notify, install-skills
├── memory/                # Persistent three-tier memory
│   ├── episodes/          # Recent observations (7-day retention)
│   ├── topics/            # Consolidated knowledge (90-day)
│   └── procedures/        # Permanent processes
├── background/            # Research background materials
├── methodology/           # Research methods + ideas
├── experiments/           # Experiment code + results
├── outputs/               # Deliverables (short/mid/long-term + paper/)
├── resources/             # Reference materials (papers/ + repos/)
├── logs/                  # experiments/ (external GPU runs) + digest/ (optional narrative logs)
└── docs/                  # Plans, reports
```

## How CLAUDE.md Works

SER is driven by `CLAUDE.md` — a behavioral protocol that Claude Code reads automatically.
It defines:

- **Intent router**: lifecycle-stage-grouped patterns that map your messages to SER skills
- **Session lifecycle**: auto-open/close with memory persistence
- **Data contracts**: standardized formats for logs, paper notes, memory files
- **Evolution loop**: G2/G1 feedback cycle for skill improvement

Each subdirectory has its own `CLAUDE.md` with scoped context for that area.
The root `CLAUDE.md` is the bootloader; subdirectory files are namespace guides.

## Typical Workflows

### Daily Research

```
(open claude)
→ session-open shows status banner

"I want to continue reading the LAPA paper"
→ paper-read generates structured notes

"Is this derivation step correct? [paste]"
→ proof (critique mode) checks it

"That's it for today"
→ session-close saves summary + evolve-suggest updates skill values
```

### Idea Exploration

```
"What are the open problems in agent memory?"
→ idea (discover mode) generates candidates

"Is the second idea novel?"
→ idea-verify checks against existing literature

"Let's go with that direction"
→ decision-analyze records the choice
```

### Paper Writing

```
"Time to start writing"
→ writing (outline mode) generates structure

"Write the introduction"
→ writing (draft mode) produces a draft

"Review this version"
→ writing-review simulates peer review (3-way if --codex-track codex)

"Compile the paper"
→ paper-assets (compile mode) runs scripts/compile_paper.sh, reports errors
```

### Experiment Lifecycle

```
"Design an experiment to test claim C"
→ experiment-plan writes claims / variables / baselines

"Sweep the learning rate and batch size"
→ experiment-dse generates configs + runs them with early stopping

"Launch it"
→ experiment-run dispatches (GPU pre-flight + SSH aware)

"Analyze the results"
→ experiment-analyze → paper-assets (figure mode) renders publication-ready plots
```

### Coding Workflow

```
"Start a branch for the ingest refactor"
→ code (branch mode) creates feat/... and (optionally) a worktree

"Plan the refactor first"
→ code (roadmap mode) breaks it into steps

"Implement step 2"
→ code-implement (with /codex:rescue fallback if --codex-track codex)

"Review the diff"
→ code-review (with /codex:review as 2nd reviewer if --codex-track codex)

"Commit"
→ code (commit mode) following shared git conventions
```

## License

MIT — See [LICENSE](LICENSE)
