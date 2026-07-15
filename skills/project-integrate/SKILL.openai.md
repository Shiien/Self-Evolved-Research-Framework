---
name: project-integrate
description: >-
  Integrate an unpacked SER v6 distribution into an existing research project.
  Inventories conflicts, installs Codex skills under .agents/skills, merges the
  AGENTS.md protocol, initializes v6 state files, and preserves user data. Use
  when asked to integrate SER, set up SER, or merge an SER distribution into a
  project.
---

# project-integrate

**Runtime**: Codex-native, single model. Perform the integration directly with
the active session and repository tools.

## Prerequisites

- An unpacked SER distribution such as `ser-vX.Y/`.
- An existing research project whose code, papers, data, and Git state must be
  preserved.

## Phase 1: Read-only inventory

1. Inspect the SER distribution and confirm these inputs:
   - `AGENTS.md`
   - `scripts/install-skills.sh`
   - `skills/`
   - `harness/` and `configs/`
   - `RESEARCH_STATE.md`, `EXPERIMENTS.json`, and `IDEA_BACKLOG.md`
   - `memory/` and supporting scripts
2. Inspect the target project for source code, papers, configs, existing
   `.agents/skills/`, `AGENTS.md`, research state, and uncommitted Git work.
3. Report every path collision before writing. Distinguish framework templates
   from user-owned state and project data.

The inventory report must state what will be copied, merged, initialized,
preserved, or skipped.

## Phase 2: Integrate framework files

Perform each operation additively and idempotently.

1. Install the Codex skill surface:

   ```bash
   mkdir -p .agents/skills
   bash ser-vX.Y/scripts/install-skills.sh \
     --runtime codex \
     --source ser-vX.Y/skills \
     --target .agents/skills
   ```

   If same-name project skills already exist, inspect them individually. Use
   `--force` only after explicit approval for those replacements.

2. Copy framework code and templates without overwriting user data:
   - `harness/` supplies deterministic experiment execution.
   - `configs/` supplies contract-bearing example configs.
   - supporting scripts and shared skill resources are copied when absent.
   - existing project code, papers, logs, runs, memory, and outputs stay in
     place.

3. Merge `AGENTS.md` with the SER protocol first and project domain knowledge
   second. Remove duplicate headings and adapt the architecture tree to the
   actual project. Preserve project-specific restrictions.

4. Initialize v6 state ownership:
   - `RESEARCH_STATE.md`: current question, hypotheses, evidence, uncertainties,
     and recommended experiments. Preserve an existing populated file.
   - `EXPERIMENTS.json`: planned, running, and resolved experiment ledger.
     Merge existing entries by stable experiment identifier.
   - `IDEA_BACKLOG.md`: out-of-scope ideas and revisit conditions.
   - `memory/`: durable non-scientific context only.
   - `Checklist.md` and `checklists/`: deliverable tracking only.

5. Create or merge `config.yaml` from the distribution template using known
   project metadata. Ask only for material values that cannot be inferred.

## Phase 3: Verify

Run these checks from the integrated project:

```bash
python -m harness setup
bash ser-vX.Y/scripts/install-skills.sh \
  --runtime codex \
  --source ser-vX.Y/skills \
  --target /tmp/ser-codex-skills \
  --force
git status --short
```

Also run the project's existing build or test command. Verify that installed
skill manifests are valid, the root protocol points to `.agents/skills/`, and
no user files were removed or silently replaced.

## Phase 4: Commit

Before committing, show the complete diff and separate framework additions
from user state. Commit only after the user approves the staged scope. Report
the resulting state owners, skill count, verification commands, and any paths
left intentionally unresolved.

## Invariants

1. Never move or delete existing project data.
2. Never replace populated state files with empty templates.
3. Skill installation is additive unless a same-name replacement is explicitly
   approved.
4. The SER protocol and project domain instructions must both remain present.
5. Experiment execution requires a valid contract and objective evaluation.
