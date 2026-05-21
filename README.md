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
| "Is this proof correct?" | `proof-critique` — step-by-step check |
| "Prove that …" | `proof-write` — first draft of the proof |
| "What should I do next?" | `plan-suggest` — prioritized tasks |
| "Design the experiment" | `experiment-plan` — claims / variables / baselines |
| "Sweep these hyperparameters" | `experiment-dse` — search strategy + configs |
| "Run the experiment" | `experiment-run` — launch + monitoring |
| "Any novel ideas for X?" | `idea-discover` → `idea-verify` → `idea-refine` |
| "Write the introduction" | `writing-draft` — section draft |
| "Plot the results as a bar chart" | `paper-figure` — PGFPlots / matplotlib |
| "Compile the paper" | `paper-compile` — pdflatex + bibtex/biber |
| "Implement this feature" | `code-roadmap` → `code-implement` → `code-review` → `code-commit` |
| (end conversation) | `session-close` — auto-saves summary |

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
1. Read your config and memory (`session-open`)
2. Show a status banner
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
bash scripts/install-skills.sh --only 'code-*,paper-figure'
bash scripts/install-skills.sh --exclude 'theory-*,proof-*'
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
When selected, the installer strictly preflights Codex CLI login +
`/codex:review` + `mcp__codex__codex` and aborts if any dep is missing.

> **Before using `--codex-track codex`:**
> - Install the **[Codex Claude Code plugin](https://github.com/openai/codex-plugin-cc)**
>   in this workspace — it provides the `/codex:review`, `/codex:rescue`,
>   `/codex:adversarial-review`, `/codex:status`, `/codex:result`,
>   `/codex:cancel` slash commands plus the `mcp__codex__codex` MCP server that
>   the Codex-track skills call.
> - Sign in once with `codex login` (ChatGPT subscription or OpenAI API key).
> - **Strongly recommended — install
>   [Superpowers](https://github.com/obra/superpowers) inside Codex** (not
>   Claude Code). Superpowers materially improves TDD / planning / review
>   quality on the Codex side. It is not preflighted by this installer because
>   it lives in Codex, but the Codex-track skills assume it when available.

Each SER skill lives in its own directory under `skills/` with a standard
`SKILL.md` (YAML frontmatter + body), so Claude Code auto-discovers and
auto-triggers them once installed.

## Skills (57 SER + 1 external)

Each skill lives in `skills/{skill-name}/SKILL.md` with standard YAML frontmatter.
Skills marked † ship both `SKILL.claude.md` and `SKILL.codex.md` variants — pick
via `--codex-track` at install time.

| Category | Skills | Purpose |
|----------|--------|---------|
| **Session** | `session-open`, `session-close` | Lifecycle: status banner, auto-save |
| **Paper reading** | `paper-read` (standard + deep/Fey-R), `paper-compare`, `paper-index`, `paper-lit-search` | Reading, comparison, arXiv + Semantic Scholar search |
| **Paper writing** | `writing-outline`, `writing-draft`, `writing-review`†, `writing-polish` | Outline → draft → peer-review → polish |
| **Paper build** | `paper-compile`, `paper-figure`, `paper-illustrate`, `paper-art` | LaTeX build, data plots, architecture diagrams, pixel art |
| **Theory** | `theory-formalize`, `theory-decompose`, `theory-search`, `theory-counterexample`, `theory-generalize` | Formalization & proof strategy |
| **Proof** | `proof-write`, `proof-critique`, `proof-fix`, `proof-formalize`, `proof-verify` | First draft → review → repair → Lean/Coq → spot-check |
| **Ideas** | `idea-discover`, `idea-verify`†, `idea-refine` | Gap analysis → novelty check → sharpened proposal |
| **Experiment** | `experiment-plan`, `experiment-dse`, `experiment-run`, `experiment-monitor`, `experiment-analyze` | Design → hyperparameter sweep → dispatch → monitor → analyze |
| **Coding** | `code-roadmap`, `code-branch`, `code-implement`†, `code-debug`, `code-review`†, `code-commit` | Plan → branch → implement → debug → review → commit |
| **Planning** | `plan-suggest`, `plan-milestone`, `progress-capture`, `status-report`, `decision-analyze` | Project management |
| **Checklist** | `checklist-create`, `checklist-verify`, `checklist-update`, `checklist-status` | Paper audit & claim tracking |
| **Research** | `research-explore`, `design-converge` | Open-ended exploration |
| **Memory** | `memory-write`, `memory-retrieve`, `memory-consolidate`, `memory-forget` | Persistent cross-session memory |
| **Meta** | `evolve-suggest`, `evolve-apply`, `general-research` | TD-NL skill self-improvement + fallback |
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

## Project Structure

```
├── CLAUDE.md              # Behavioral protocol (intent router + data contracts)
├── config.template.yaml   # Copy to config.yaml and customize
├── README.md / LICENSE
├── skills/
│   ├── {skill-name}/      # 57 SER skills, each with SKILL.md + YAML frontmatter
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
├── scripts/               # Utility scripts (citation, notify, analyzer, install-skills)
├── memory/                # Persistent three-tier memory
│   ├── episodes/          # Recent observations (7-day retention)
│   ├── topics/            # Consolidated knowledge (90-day)
│   └── procedures/        # Permanent processes
├── background/            # Research background materials
├── methodology/           # Research methods + ideas
├── experiments/           # Experiment code + results
├── outputs/               # Deliverables (short/mid/long-term + paper/)
├── resources/             # Reference materials (papers/ + repos/)
├── logs/digest/           # Session logs
└── docs/                  # Plans, reports
```

## How CLAUDE.md Works

SER is driven by `CLAUDE.md` — a behavioral protocol that Claude Code reads automatically.
It defines:

- **Intent router**: 40 patterns that map your messages to SER skills
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
→ proof-critique checks it

"That's it for today"
→ session-close saves summary + evolve-suggest updates skill values
```

### Idea Exploration

```
"What are the open problems in agent memory?"
→ idea-discover generates candidates

"Is the second idea novel?"
→ idea-verify checks against existing literature

"Let's go with that direction"
→ decision-analyze records the choice
```

### Paper Writing

```
"Time to start writing"
→ writing-outline generates structure

"Write the introduction"
→ writing-draft produces a draft

"Review this version"
→ writing-review simulates peer review (3-way if --codex-track codex)

"Compile the paper"
→ paper-compile runs pdflatex + bibtex/biber, reports errors
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
→ experiment-analyze → paper-figure renders publication-ready plots
```

### Coding Workflow

```
"Start a branch for the ingest refactor"
→ code-branch creates feat/... and (optionally) a worktree

"Plan the refactor first"
→ code-roadmap breaks it into steps

"Implement step 2"
→ code-implement (with /codex:rescue fallback if --codex-track codex)

"Review the diff"
→ code-review (with /codex:review as 2nd reviewer if --codex-track codex)

"Commit"
→ code-commit following shared git conventions
```

## License

MIT — See [LICENSE](LICENSE)
