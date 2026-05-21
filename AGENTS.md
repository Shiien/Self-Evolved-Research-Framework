# AGENTS.md - SER Codex Runtime

You are running SER inside Codex.

SER is a behavior-driven research collaboration framework. It routes natural-language research requests to local skills under `.agents/skills/`, maintains project memory, tracks checklists, and can evolve skill instructions from session feedback.

## Runtime Rules

- Use Codex-native skills from `.agents/skills/`.
- Treat `AGENTS.md` as the root behavioral protocol.
- Do not depend on Claude Code runtime files, `.claude/skills`, `/codex:*` delegation commands, or `mcp__codex__codex`.
- Use the active Codex session as the single model for implementation, review, writing, and verification.

## Project Flow

1. Read `config.yaml` when present.
2. Read `memory/MEMORY.md` when present.
3. Use `Checklist.md` and `checklists/` as the progress source of truth.
4. Route user intent to the matching skill when a skill's description applies.
5. Write durable outputs to the project directories declared in this repository.

## Skill Loading

Installed Codex skills live in `.agents/skills/{skill-name}/SKILL.md`.

If a task matches a skill, follow that skill's instructions. If no specific skill applies, use `general-research` behavior: clarify the user's goal, gather evidence, and produce a concrete next action.

## Repository Boundaries

- Keep edits scoped to the active research project.
- Do not rewrite framework instructions unless the user asks to modify SER itself.
- Preserve user work and do not remove untracked files without explicit permission.
