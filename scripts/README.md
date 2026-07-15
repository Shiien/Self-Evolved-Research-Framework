# Scripts - Helper Scripts

This directory contains Python scripts that support the SER framework, mainly to **reduce token usage**.

## Script List

### `install-skills.sh` - Install Bundled Skills for Claude or Codex

**Purpose**: Auto-discover every skill under `./skills/` (any directory containing
`SKILL.md`, `SKILL.claude.md`, or `SKILL.openai.md`) and install it for one
selected single-model runtime. Claude selects `SKILL.claude.md` before
`SKILL.md` and installs to `.claude/skills/`; Codex selects
`SKILL.openai.md` before `SKILL.md` and installs to `.agents/skills/`.
Runtime-native manifests are materialized as installed `SKILL.md` files.
Non-skill directories like `skills/_shared/` and `skills/td-nl/` are skipped
because they have no skill manifest.

**Usage**:
```bash
bash scripts/install-skills.sh                 # copy into ./.claude/skills
bash scripts/install-skills.sh --runtime claude # explicit form of the default
bash scripts/install-skills.sh --runtime codex # copy into ./.agents/skills
bash scripts/install-skills.sh --link          # link neutral Claude manifests
bash scripts/install-skills.sh --user          # install to ~/.claude/skills (Claude runtime only)
bash scripts/install-skills.sh --dry-run       # preview without writing
bash scripts/install-skills.sh --list          # list discovered skills
bash scripts/install-skills.sh --force         # overwrite existing installs
bash scripts/install-skills.sh --help          # full option reference
```

Safe to re-run; existing installs are skipped unless `--force` is passed.
With Claude `--link`, neutral manifests are symlinked while runtime-native
manifests are materialized as copies. Codex uses project-local materialized
copies only, so its runtime rejects `--link` and `--user`.

---

### `skill_analyzer.py` - Optional Legacy Usage Diagnostic

**Purpose**: Incrementally scan historical skill-invocation logs and emit a
structured report for manual diagnostics. This script is retained for legacy
log inspection; its output is **not** a canonical v6 skill-evolution input and
does not update Q^L, create pending flags, propose edits, or apply changes.

**Usage**:
```bash
python scripts/skill_analyzer.py
```

**Output**:
- `logs/analysis/skills_stats.json` — optional diagnostic report
- `logs/analysis/last_processed.txt` — incremental scan marker

The canonical v6 path is independent of this analyzer:

1. A real reward signal triggers signal-gated `skill-feedback`.
2. `skill-feedback` performs the online EWMA Q update and may write a pending
   flag.
3. A user-requested audit, or an explicit session-close opt-in, runs
   `evolve-suggest` over pending flags and derived V^L.
4. Only user-approved proposals reach `evolve-apply`, which archives before
   editing and supports approved rollback.

---

## Install Dependencies

```bash
pip install -r scripts/requirements.txt
```
