---
name: project-integrate
description: Merge an unpacked SER distribution (ser-vX.Y/) into an existing research project — inventory conflicts, copy framework dirs, install Codex skills under .agents/skills, merge AGENTS.md, create config.yaml, and seed memory. Triggers on "integrate SER", "set up SER for this project", "merge SER into this repo".
---

# project-integrate

**Trigger**: User says "integrate SER", "merge into SER framework", "set up SER for this project", or has an unpacked `ser-vX.Y/` directory alongside their existing research project.

## Prerequisites

- An unpacked SER distribution (e.g., `ser-vX.Y/`) in or near the project root
- An existing research project with code, papers, or data already present

## Process

### Phase 1: Inventory (read-only)

1. **Scan SER pack**: Read `ser-vX.Y/MANIFEST.yaml` to identify all framework files
2. **Scan existing project**: Identify the project's key assets:
   - Source code directories (Python, LaTeX, configs)
   - Paper/document files (.tex, .pdf, .md)
   - Existing `.agents/` configuration (skills/)
   - Existing `AGENTS.md` with project instructions
   - Git state (branch, uncommitted changes)
3. **Detect conflicts**: Check if any SER directory names already exist in project root:
   - `memory/`, `logs/`, `resources/papers/`, `background/`, `methodology/`, `outputs/`, `resources/`, `scripts/`
   - `.agents/skills/`, `config.yaml`, `AGENTS.md`
4. **Report inventory** to user:
   ```
   === SER Integration Inventory ===
   SER version: vX.Y
   Project: {name from existing AGENTS.md or git remote}

   Existing assets found:
   - {list of code dirs, paper files, configs}

   Conflicts: {none | list of conflicting paths}

   Will copy: {N} framework dirs, {M} config files
   Will merge: AGENTS.md, .agents/skills
   Will create: config.yaml, memory/MEMORY.md, logs/digest/SUMMARY.md
   Will preserve: {all existing project files stay in place}
   ```

### Phase 2: Copy Framework (4 sub-steps)

Execute these in order. Each is idempotent (safe to re-run).

#### 2.1: Copy SER directories

```bash
# From project root:
mkdir -p .agents/skills
bash ser-vX.Y/scripts/install-skills.sh \
  --runtime codex \
  --source ser-vX.Y/skills \
  --target .agents/skills
cp -rn ser-vX.Y/memory .          # Memory system (templates)
cp -rn ser-vX.Y/scripts .         # Utility scripts
# Create empty SER directories (only if they don't exist):
for dir in logs/digest background methodology \
           resources/papers; do
  mkdir -p "$dir"
  [ ! -f "$dir/.gitkeep" ] && touch "$dir/.gitkeep"
done
```

**Rule**: Never overwrite existing directories that contain user data. If `.agents/skills/` already has project-specific skills, merge SER skills additively and review same-name skill conflicts before replacing anything. If the installer reports skipped existing skills, inspect each conflict and rerun with `--force` only after explicit user approval. If `resources/papers/` already has files, only add `.gitkeep` if missing.

#### 2.2: Merge AGENTS.md

Create a two-part document:

```markdown
# SER vX.Y — Behavioral Protocol
{entire contents of ser-vX.Y/AGENTS.md}

# {Project Name} — Domain Knowledge
{entire contents of existing AGENTS.md}
```

**Rules**:
- SER protocol section comes FIRST (it must be read first for runtime behavior)
- Remove duplicate headings if the existing AGENTS.md also has `# AGENTS.md` as H1
- Update the "Project Architecture" tree in SER section to reflect actual project structure

#### 2.3: Create config.yaml

Fill the template from `ser-vX.Y/config.yaml` with project-specific values. Ask user for:
- Project name and domain/keywords
- Timeline (start date, duration, milestones)
- Current status (what's done, what's next)

If the existing AGENTS.md contains this information, extract it automatically.

#### 2.4: Initialize memory

**MEMORY.md**: Populate Active Context with:
- Current project focus (from AGENTS.md or user input)
- Key asset paths (code dirs, paper files)
- Project status (what's done, what's in progress)

**Seed episodes**: Create 1-3 episodes in `memory/episodes/`:
- `YYYY-MM-DD-001.md`: Project overview (assets, architecture, goals)
- `YYYY-MM-DD-002.md`: Key decisions made before SER integration (if any)


**SUMMARY.md**: Create empty session log index:
```markdown
# Session Log Summary

| Date | Type | Summary | Phase | Token Est |
|------|------|---------|-------|-----------|
```

### Phase 3: Verify

1. **Structure check**: Verify all SER skill directories exist under `.agents/skills/`
2. **Memory check**: Verify `memory/MEMORY.md` has Active Context filled
3. **Build check**: If project has a build step (LaTeX compile, test suite), run it to confirm nothing broke
4. **Git check**: `git status` to show all new/modified files before committing

### Phase 4: Commit

Stage and commit with message format:
```
Integrate SER vX.Y framework for structured research workflow

- {N} micro-skill directories covering session, paper, theory, proof, writing, planning, meta, research, memory
- Codex skill installation under .agents/skills
- Memory system with Options Framework + TD-NL optimization
- Project config with timeline and milestones
- Merged AGENTS.md (SER protocol + project domain knowledge)
- Seeded memory with {M} initial episodes
```

## Key Principles

1. **Never move existing files**. Project code, papers, and data stay exactly where they are. SER adds structure around them.
2. **Never overwrite user data**. If a directory/file exists with user content, merge or append — never replace.
3. **Skill installation is additive**. Merge skill directories, never remove existing project skills.
4. **AGENTS.md is merged, not replaced**. Both SER protocol and project knowledge must be present.
5. **Memory seeds from existing state**. Don't start cold — extract what's known from AGENTS.md, git log, and directory structure.

## Output

- Integrated project with SER framework directories
- Merged AGENTS.md + .agents/skills
- Populated config.yaml + memory/MEMORY.md
- Ready for first `session-open` in next conversation

## Token Cost

~3-5K (mostly file copying + config generation)
