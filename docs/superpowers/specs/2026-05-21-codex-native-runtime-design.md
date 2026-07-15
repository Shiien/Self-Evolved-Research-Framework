# Codex-Native Runtime Design

Date: 2026-05-21
Branch: `feat/codex-native-runtime`
Status: Design approved for implementation planning

## Goal

Add a Codex-native runtime path to SER while preserving the existing Claude
Code runtime exactly as-is.

The Codex runtime is single-model and single-agent by default. It should behave
like the current Track A semantics: the active Codex session performs the work
directly. It must not use the existing Claude Code Track B semantics that
delegate to `/codex:*`, add Codex as a second reviewer, or require
`mcp__codex__codex`.

## Non-Goals

- Do not remove or rewrite the existing Claude Code runtime.
- Do not remove `--codex-track claude|codex` for Claude Code installs.
- Do not make the Codex runtime dual-model.
- Do not require Claude Code, `/codex:*`, or `mcp__codex__codex` for Codex-native
  installs.
- Do not manually rewrite every skill when a skill is already runtime-neutral.

## Runtime Model

SER will support two runtime families:

```text
Claude Code runtime
  Entry point:    CLAUDE.md
  Skill target:   .claude/skills/
  Variants:       SKILL.md, SKILL.claude.md, SKILL.codex.md
  Track support:  --codex-track claude|codex

Codex runtime
  Entry point:    AGENTS.md
  Skill target:   .agents/skills/
  Variants:       SKILL.openai.md, SKILL.md
  Track support:  single-model only; no --codex-track
```

OpenAI Codex uses `AGENTS.md` for repository instructions and supports local
skills under `.agents/skills/`, where each skill directory contains a
`SKILL.md`. References:

- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/skills

## Skill Variant Semantics

Existing variant meanings remain unchanged:

- `SKILL.md`: runtime-neutral default.
- `SKILL.claude.md`: Claude Code Track A.
- `SKILL.codex.md`: Claude Code Track B, meaning Claude Code augmented by Codex.

New variant:

- `SKILL.openai.md`: Codex-native single-model version.

The name `SKILL.openai.md` is intentionally distinct from `SKILL.codex.md` so
the current Claude Code Track B meaning remains stable.

## Installer Behavior

`scripts/install-skills.sh` gains a runtime axis:

```bash
bash scripts/install-skills.sh --runtime claude --codex-track claude
bash scripts/install-skills.sh --runtime claude --codex-track codex
bash scripts/install-skills.sh --runtime codex
```

Backward compatibility:

- Omitting `--runtime` defaults to `claude`.
- Existing Claude Code commands keep their current behavior.

Selection rules:

```text
runtime=claude, --codex-track claude:
  SKILL.claude.md > SKILL.md

runtime=claude, --codex-track codex:
  SKILL.codex.md > SKILL.claude.md > SKILL.md

runtime=codex:
  SKILL.openai.md > SKILL.md
```

Codex install validation:

- `--runtime codex --codex-track ...` is invalid.
- `--runtime codex` writes to `.agents/skills/`.
- `--runtime codex --user` is invalid for the first version unless a stable
  Codex user-skill install target is introduced in a separate approved design.
- Codex mode never selects `SKILL.codex.md`.

## Full Install Surface Requirement

The first implementation must cover the complete installed skill surface, not
only a hand-picked subset.

For every skill directory:

1. If `SKILL.openai.md` exists, install it as `SKILL.md`.
2. Else if `SKILL.md` is runtime-neutral, install it as-is.
3. Else add `SKILL.openai.md` or make the source skill runtime-neutral before
   allowing Codex installation to pass.

Codex installation must fail or warn loudly if installed skills retain obvious
Claude Code runtime coupling.

## Runtime-Coupling Audit

Add an audit step for `--runtime codex`, at least in dry-run output and ideally
as a hard failure unless explicitly bypassed.

Forbidden markers in installed `.agents/skills/*/SKILL.md`:

- `Claude Code`
- `.claude`
- `CLAUDE.md`
- `/codex:`
- `mcp__codex__codex`

Allowed cases require an explicit inline context that the skill is documenting
interop or migration behavior rather than depending on Claude Code at runtime.

## Codex Entry Point

Add root `AGENTS.md` as a Codex-native adaptation of `CLAUDE.md`.

It should:

- Define SER's intent-routing behavior for Codex.
- Refer to `.agents/skills/` instead of `.claude/skills/`.
- Refer to `AGENTS.md` as the repository instruction file.
- Avoid Claude-specific lifecycle language.
- Keep the same project structure, memory, checklist, research workflow, and
  skill-trigger semantics.

Directory-local `CLAUDE.md` files can remain for Claude Code. Codex-specific
directory-local `AGENTS.md` files are optional and should only be added where
root `AGENTS.md` is insufficient.

## Initial Codex-Native Variants

The variant audit decides the final list, but the following skills are known to
need Codex-native variants or neutralization because they currently have
runtime-specific behavior:

- `code-implement`
- `code-review`
- `writing-review`
- `idea-verify`
- `project-integrate`
- any skill or test helper that writes or assumes `.claude/skills`
- any skill that instructs use of `/codex:*` or `mcp__codex__codex`

Codex-native versions should preserve Track A-style single-model semantics.

Examples:

- `code-implement`: Codex implements directly using TDD and roadmap discipline;
  no `/codex:rescue`.
- `code-review`: Codex reviews directly; no second reviewer by default.
- `writing-review`: Codex simulates peer review directly; no dual-model loop.
- `idea-verify`: Codex synthesizes DBLP/arXiv/local evidence directly; no Codex
  reviewer as an extra source.

## Documentation Updates

Update:

- `README.md`
- `README.zh-CN.md`
- `scripts/README.md`
- `scripts/CLAUDE.md`

Docs must explain:

- Claude Code runtime remains supported.
- Codex runtime is new and single-model.
- Claude Code `--codex-track codex` is not the same as Codex-native runtime.
- How to install each runtime.

## Tests

Installer tests should cover:

```bash
bash scripts/install-skills.sh --dry-run --runtime claude --codex-track claude
bash scripts/install-skills.sh --dry-run --runtime claude --codex-track codex
bash scripts/install-skills.sh --dry-run --runtime codex
```

Codex install assertions:

```bash
bash scripts/install-skills.sh --runtime codex --force
test -f .agents/skills/code-implement/SKILL.md
test ! -f .agents/skills/code-implement/SKILL.codex.md
test ! -d .claude/skills/code-implement
```

Audit assertions:

```bash
rg 'Claude Code|\.claude|CLAUDE\.md|/codex:|mcp__codex__codex' .agents/skills
```

The audit should either return no hits or only explicitly allowlisted migration
documentation hits.

## Rollout Plan

1. Create the branch `feat/codex-native-runtime`.
2. Add `AGENTS.md`.
3. Extend `scripts/install-skills.sh` with `--runtime`.
4. Add Codex install audit.
5. Add or neutralize Codex-native variants until the full `.agents/skills/`
   install surface passes audit.
6. Update documentation.
7. Run installer dry-run and real install checks for both runtimes.

## Success Criteria

- Claude Code install behavior remains backward compatible.
- `--runtime codex` installs all eligible SER skills to `.agents/skills/`.
- Codex install never selects Claude Code Track B `SKILL.codex.md`.
- Installed Codex skills are Codex-native or runtime-neutral.
- No installed Codex skill depends on Claude Code, `.claude`, `/codex:*`, or
  `mcp__codex__codex`.
- README clearly distinguishes Claude Code Track B from Codex-native runtime.
