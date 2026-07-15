# Scripts - Helper Scripts

This directory contains Python scripts that support the SER framework, mainly to **reduce token usage**.

## Script List

### `install-skills.sh` - Install Bundled Skills for Claude or Codex

**Purpose**: Auto-discover every skill under `./skills/` (any directory containing
`SKILL.md`, `SKILL.claude.md`, `SKILL.codex.md`, or `SKILL.openai.md`) and install
it for the selected runtime. Claude runtime installs to `.claude/skills` so Claude
Code can load the skills; Codex runtime installs to `.agents/skills` so Codex can
load materialized OpenAI-native skills. Runtime variant files are materialized as
installed `SKILL.md` files. Non-skill directories like `skills/_shared/` and
`skills/td-nl/` are skipped because they have no skill spec file.

**Usage**:
```bash
bash scripts/install-skills.sh                 # copy into ./.claude/skills
bash scripts/install-skills.sh --runtime claude --codex-track claude
bash scripts/install-skills.sh --runtime claude --codex-track codex
bash scripts/install-skills.sh --runtime codex # copy into ./.agents/skills
bash scripts/install-skills.sh --link          # symlink (Claude runtime only)
bash scripts/install-skills.sh --user          # install to ~/.claude/skills (Claude runtime only)
bash scripts/install-skills.sh --dry-run       # preview without writing
bash scripts/install-skills.sh --list          # list discovered skills
bash scripts/install-skills.sh --force         # overwrite existing installs
bash scripts/install-skills.sh --help          # full option reference
```

Safe to re-run; existing installs are skipped unless `--force` is passed.
`--link`, `--user`, and `--codex-track` are Claude-runtime-only options; Codex
runtime rejects them because it requires project-local materialized skill copies.

---

### `skill_analyzer.py` - Skill Usage Statistics Analyzer

**Purpose**: Incrementally scan Skill invocation logs and generate a structured statistics report

**Usage**:
```bash
python scripts/skill_analyzer.py
```

**Output**:
- `logs/analysis/skills_stats.json` - statistics report (read by `/skill-evolve`)
- `logs/analysis/last_processed.txt` - last processed position (incremental marker)

**Token Savings**:
- Traditional approach: `/skill-evolve` needs 20-30K tokens to read and analyze logs
- Script-based approach: only 3-5K tokens to read the JSON report
- **Roughly 80% savings**

---

## Install Dependencies

```bash
pip install -r scripts/requirements.txt
```

---

## Integrating with /skill-evolve

`/skill-evolve` execution flow:

```
1. [Bash] Run `python scripts/skill_analyzer.py`
    ↓
2. [Read] Read `logs/analysis/skills_stats.json` (cost <1K tokens)
    ↓
3. [Claude] Present the report + user interaction (cost 8-15K tokens)
    ↓
4. [Claude] Generate improvement actions + update files (cost 5-10K tokens)
```

**Total cost**: 13-25K tokens (about 25-40% less than the original 20-30K)

---

## Data Model

### Skill ID Mapping

Each Skill has a unique ID:

```python
SKILL_IDS = {
    # Meta layer
    "research-init": "meta_001",
    "background-builder": "meta_002",
    ...

    # Object layer
    "problem-decompose": "research_001",
    "proof-refine": "research_004",
    ...
}
```

### Log Format Requirements

Each Skill log file should include the following fields (used for analytics):

```yaml
# logs/research-skills/{skill_name}/YYYY-MM-DD_NNN.yaml

metadata:
  skill_id: "research_004"  # unique identifier
  timestamp: "2026-02-15 14:30"

token_consumption:
  actual: 25000

user_satisfaction: 5  # 1-5

variant_used: "deep"  # if a variant was used
variant_winner: "deep"  # if that variant won
```

---

## Future Extensions

- [ ] Support extracting Skill calls from Claude conversation logs (via pattern matching)
- [ ] Time-series analysis (token usage trends, satisfaction changes)
- [ ] Automatically generate variant suggestions (based on failure patterns)

---

*Version: 1.0*
