---
name: code-roadmap
description: Write a step-by-step implementation roadmap for a non-trivial coding task — Goal, Context, Constraints, 3-8 Steps (each with Files/What to do/Acceptance), Done Criteria, Status. Saves to `docs/implement_roadmap/YYYY-MM-DD-{name}.md` and writes the path back into the driving checklist checkbox. Triggers when a medium/large coding task needs structured planning before execution, or when the user asks "make a plan for implementing X", "write the implementation roadmap", "design a plan for {feature}".
---

# code-roadmap

**Trigger**: A medium/large coding task needs structured planning before execution. Typical entry point is a checklist L2 Method `[ ] Implementation — {path}` checkbox being expanded.

**Shared context**: None.

**Pair with**: `code-implement` (the skill that executes the roadmap, Track A or B).

## Process

### Step 1 — Understand the Goal

- Read the user's request. If ambiguous, ask clarifying questions before writing.
- Read existing relevant source files to understand current architecture, interfaces, conventions.
- Read `methodology/approach.md` (if it exists) to anchor terminology.
- Identify the test framework and test command in current use.

### Step 2 — Create the directory

```bash
mkdir -p docs/implement_roadmap
```

### Step 3 — Write the roadmap file

Save to `docs/implement_roadmap/YYYY-MM-DD-{feature-name}.md`. Follow the format below exactly — every section is mandatory.

---

#### Roadmap File Format

````markdown
# Roadmap: {Feature Name}

## Goal

{One clear sentence: what this roadmap achieves when fully completed.}

## Context

- **Project**: {project name + one-line description}
- **Language / Framework**: {e.g., Python 3.11, PyTorch 2.x, pytest}
- **Test command**: {e.g., `pytest tests/ -v`}
- **Key files for context** (read these to understand the codebase):
  - `{path}` — {what this file does and why it matters}
  - `{path}` — {what this file does and why it matters}

## Constraints

- Do NOT modify: `.agents/`, `skills/`, `memory/`, `hooks/`, `config.yaml`, `AGENTS.md`
- Do NOT run `git commit` or `git push` during execution
- Do NOT add new dependencies unless explicitly justified in a step
- {Any project-specific constraints — e.g., "must be backward-compatible with existing config format"}

## Steps

### Step 1: {Descriptive title}

- **Purpose**: {Why this step is needed — the problem it solves or the capability it adds}
- **Files**:
  - Create: `{path}` — {what this file will contain}
  - Modify: `{path}` — {what changes and why}
  - Test: `{path}` — {test file for this step}
- **What to do**: {Concrete description at function/class/module level. Describe interfaces, expected behavior, edge cases. Do NOT write code — describe what the code should do.}
- **Acceptance**:
  - `{test command}` passes with all new tests green
  - {Any additional verifiable condition — e.g., "`python -c 'from module import X'` succeeds"}

### Step 2: {Descriptive title}

- **Purpose**: ...
- **Files**: ...
- **What to do**: ...
- **Acceptance**: ...

{Continue for all steps. Typical roadmaps have 3-8 steps.}

## Done Criteria

When the entire roadmap is complete, ALL of the following must be true:

1. `{full test command}` — all tests pass, zero failures
2. {Functional verification — e.g., "running `python main.py --config test.yaml` produces expected output"}
3. {Integration check — e.g., "existing tests in `tests/test_old.py` still pass (no regressions)"}

## Status

- [ ] Step 1: {title}
- [ ] Step 2: {title}
- [ ] ...
- **Base commit**: {SHA to be filled by code-implement before first execution}
- **Last updated**: {YYYY-MM-DD}
````

---

### Step 4 — Roadmap Quality Checklist

Before presenting the roadmap, verify:

- [ ] Goal is one sentence, describes end state (not process)
- [ ] Context lists the test command verbatim
- [ ] Key files are actual paths that exist in the repo
- [ ] Constraints explicitly forbid SER framework dirs
- [ ] Each step has all four fields (Purpose / Files / What to do / Acceptance)
- [ ] Each step's Acceptance is a runnable command or verifiable condition
- [ ] Done Criteria combines (a) full test suite, (b) functional check, (c) regression check
- [ ] Typical step count is 3-8; if fewer than 3, the task may not need a roadmap; if more than 8, consider splitting into sub-roadmaps

### Step 5 — Write path back to source checkbox

If this roadmap was triggered by a checklist L2 Method `[ ] Implementation` checkbox, append the roadmap path as the checkbox's artifact reference:

```markdown
- [ ] Implementation — `docs/implement_roadmap/YYYY-MM-DD-{name}.md`
```

Use `checklist-update` to make this edit.

## Output

```
[code-roadmap] Created: docs/implement_roadmap/YYYY-MM-DD-{name}.md
  Steps: {N}
  Test command: {cmd}
  Ready for: code-implement
```

**Inputs**: User goal + existing source files + methodology/approach.md + (optional) driving checklist checkbox
**Outputs**: `docs/implement_roadmap/YYYY-MM-DD-{name}.md`; optional checkbox artifact update
**Token**: ~3-8K (depends on number of steps and context size)
**Composition**:
- Roadmap ready → suggest `code-implement` to execute
- Triggered from checklist → chain `checklist-update` to record the artifact path
