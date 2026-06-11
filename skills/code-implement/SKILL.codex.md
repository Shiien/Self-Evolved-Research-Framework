---
name: code-implement
description: Write or modify code with strict TDD discipline. Small tasks are handled by Claude directly (Red-Green-Refactor). Medium/large tasks read `docs/implement_roadmap/YYYY-MM-DD-{name}.md` and are delegated to the `codex:codex-rescue` subagent via the Agent tool (flags `--write --fresh [--background]`) using a four-tag prompt contract; Codex runs TDD internally via its own Superpowers. SER framework files always stay with Claude. Triggers on "implement X", "add feature Y", "execute the roadmap", or any code-writing request after a roadmap is ready.
---

# code-implement (Track B — Codex delegated)

**Trigger**: User wants to write new code or modify existing code, in a SER installation where `/codex:rescue` is available.

**Shared context**: Before delegating to Codex, Read `skills/_shared/codex-contract.md` for the prompt contract, invocation rules, background threshold, and error handling.

**Track**: B (Codex executor for medium/large; Claude for small and framework files). Installed via `./scripts/install-skills.sh --codex-track codex`. For Track A semantics (Claude direct TDD everywhere), see `SKILL.claude.md`.

---

## Step 0 — Red Flags (read before acting)

Stop and reconsider if any of these thoughts appear:

| Thought | Reality |
|---------|---------|
| "This is just simple code" | Simple things become complex. Use TDD. |
| "I'll test after" | Tests written after pass immediately, prove nothing. |
| "Should work now" | Not verification. Run the command, read output. |
| "Too simple for review" | All code gets reviewed. No exceptions. |
| "Let me explore first" | TDD IS the exploration. Write a failing test. |
| "3+ fixes failed, let me try once more" | Architecture problem. Stop and discuss. |

---

## Step 1 — Size & Executor Assessment

Two independent dimensions.

### Size

| Signal | Size |
|--------|------|
| Localized change, single file, < ~30 lines of new logic | **Small** |
| New module, multiple files, significant new logic (30–200+ lines) | **Medium/Large** |
| User explicitly requests a plan or design review | **Medium/Large** |

Default to **Small**. When uncertain, ask.

### Executor

| Signal | Executor |
|--------|----------|
| Small size | **Claude** (Codex not invoked for small tasks) |
| Change touches SER framework (`.claude/`, `skills/`, `hooks/`, `config.yaml`, `CLAUDE.md`) | **Claude** (always, regardless of size) |
| `/codex:setup` runtime check fails | **Claude** (graceful degradation — see Step 4e) |
| All other Medium/Large changes | **Codex** |

If size = Medium/Large and no roadmap exists yet, invoke `code-roadmap` first, then return here.

---

## Step 2 — Small task (executor = Claude)

Identical to Track A Step 2. Single RIGID Red-Green-Refactor cycle:

1. **RED**: Write failing test next to source. Confirm it fails for the right reason.
2. **GREEN**: Minimal code to pass.
3. **REFACTOR**: Clean up, keep tests green.

### Rules
- Run tests after every change.
- Baseline existing tests first if any exist.
- "I'll test after" is forbidden.
- Three failed fix attempts → stop, question architecture.

---

## Step 3 — Medium/Large with Framework-File Guard (executor = Claude)

If the roadmap touches SER framework paths listed under Executor signals, Codex must NOT be invoked — Codex's `action_safety` tag forbids those paths anyway. Claude executes the roadmap step-by-step using Track A Step 3 semantics (pre-flight → per-step TDD → Done Criteria).

---

## Step 4 — Medium/Large delegated to Codex

### Step 4a — Pre-flight

1. `git diff --stat` — must be empty. If not, ask user to commit or stash.
2. `git stash list` — note any stashes.
3. `git rev-parse HEAD` — record base SHA.
4. Open `docs/implement_roadmap/YYYY-MM-DD-{name}.md`.
5. Write the base SHA into Status under `Base commit:`. Update `Last updated:`.
6. Runtime Codex check: invoke `/codex:setup`. If it fails (auth expired, service down, CLI missing), jump to **Step 4e** (Claude fallback).

### Step 4b — Construct the prompt

Follow `skills/_shared/codex-contract.md § 2–3`. Four tags in order:

- `<task>` — fill from roadmap: Goal line, Key files, Steps overview (one line per step), Test command.
- `<completeness_contract>` — fixed body from the contract file.
- `<default_follow_through_policy>` — fixed body.
- `<action_safety>` — fixed body (forbidden paths + no `git commit`/`git push`).

Do not omit any tag. Do not reorder.

### Step 4c — Invoke

Per `skills/_shared/codex-contract.md § 4`, from Claude's main session Codex is ONLY reachable via the `Agent` tool with `subagent_type: "codex:codex-rescue"`. Do NOT call the `Skill` tool with `codex:rescue` and do NOT emit the literal `/codex:rescue ...` slash-command string — both paths return success without spawning a Codex job.

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Codex — {short roadmap name}",
  prompt: "--write --fresh [--background]\n\n{full four-tag prompt built in Step 4b}"
})
```

`--write` and `--fresh` are mandatory. The flags can appear anywhere in the `prompt`; the subagent strips them before forwarding to `codex-companion.mjs task`.

Background flag:

| Signal | Flag |
|---|---|
| Roadmap has ≤ 3 steps OR estimated < 5 min | foreground (default) |
| Roadmap has > 3 steps OR estimated > 5 min | add `--background` |

If `--background` is used, tell the user Codex is working and the session can proceed.

### Step 4c.v — Verify the call landed (takes seconds, catches silent failures)

Immediately after the `Agent` call returns, sanity-check that Codex actually started:

```bash
ls -lt /tmp/codex-companion/*/jobs/ 2>/dev/null | head -5
```

If no job file was created in the last minute, the invocation used the wrong channel (see `skills/_shared/codex-contract.md § 5` last row). Do NOT retry the Skill tool or the slash-command string — the bug is the channel, not Codex. Re-invoke via `Agent` exactly as shown above.

### Step 4d — Post-invocation

Per `skills/_shared/codex-contract.md § 6`:

1. Read Codex's final report. Note reported-complete steps, issues, out-of-scope modifications.
2. `git diff --stat` sanity check.
3. Do NOT self-fix issues found. They are deferred to `code-review`.
4. Update roadmap Status: `[x]` for completed steps, `[!]` with one-line note for steps Codex reported blocked. Update `Last updated:`.

### Step 4e — Claude fallback (Codex unavailable / framework file)

When `/codex:setup` fails, or the roadmap touches framework paths, Claude executes the roadmap step-by-step using Track A Step 3b/3c procedure:

- Per step: RED → GREEN → Acceptance → REFACTOR → Status update.
- After all steps: run each Done Criterion.

Announce the fallback to the user:
```
[code-implement / codex] Codex unavailable — falling back to Claude.
  Cause: {error from /codex:setup}
  Roadmap will still be followed step-by-step.
  To recover Codex path: run /codex:setup, then re-invoke for remaining steps.
```

---

## Step 5 — Done Criteria

After Codex (or fallback Claude) completes all steps:

1. Run each Done Criterion from the roadmap.
2. All pass → flow proceeds to `code-review`.
3. Any fails → mark related step `[!]`, surface to user.

---

## Output

```
[code-implement / codex] {small|roadmap-codex|roadmap-fallback} execution complete
  Executor: {claude | codex}
  Steps: {k}/{K} completed
  Ready for: code-review
```

**Inputs**: User request OR `docs/implement_roadmap/YYYY-MM-DD-{name}.md`; `skills/_shared/codex-contract.md`
**Outputs**: Code + test files; updated roadmap Status; Codex output log (if invoked)
**Token**: ~3-15K (small) / ~4-12K Claude-side for prompt + post-processing (Codex-side usage is separate)
**Composition**:
- Completes → `code-review`
- Codex reports a step blocked, cause unclear → `code-debug`
- Codex unavailable → fallback to Claude (same skill, Step 4e)
