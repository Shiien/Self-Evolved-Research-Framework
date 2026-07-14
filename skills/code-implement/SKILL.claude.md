---
name: code-implement
description: Write or modify code via strict Red-Green-Refactor TDD. For small tasks, performs a single TDD cycle directly. For medium/large tasks, reads `docs/implement_roadmap/YYYY-MM-DD-{name}.md` and executes each step with its own TDD cycle, updating the roadmap Status `[x]` after each step passes. Triggers on "implement X", "add feature Y", "change behavior of Z", or any request to write/modify code. Works on the current branch/worktree prepared by `code` (branch mode).
---

# code-implement (Track A — Claude native)

**Trigger**: User wants to write new code or modify existing code.

**Shared context**: None at this stage; if a roadmap is used, that file carries the spec.

**Track**: A (Claude direct TDD). Installed via `./scripts/install-skills.sh --codex-track claude`. For Track B semantics (Codex executor), see the codex-track variant installed at `SKILL.codex.md`.

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

## Step 1 — Size Assessment

Estimate the scope:

| Signal | → Path |
|--------|--------|
| Localized change, single file, < ~30 lines of new logic | **Small** → Step 2 |
| New module, multiple files, or significant new logic (30–200+ lines) | **Medium/Large** → requires roadmap, Step 3 |
| User explicitly requests a plan or design review | **Medium/Large** → Step 3 |
| Change touches SER framework (`.claude/`, `skills/`, `hooks/`, `config.yaml`, `CLAUDE.md`) | **Small + Claude handles directly** → Step 2 |

Default to **Small**. When uncertain, ask the user:
> "This looks like it could be [small / medium]. Should I implement it directly, or write a roadmap first?"

If Medium/Large and no roadmap exists yet, invoke `code` (roadmap mode) first, then return here.

---

## Step 2 — Small Task: single TDD cycle

Process (RIGID — no exceptions):

1. **RED**: Write a failing test that defines the expected behavior.
   - Test file lives next to source (`src/foo.py` → `tests/test_foo.py`), or in a `tests/` mirror.
   - Run the test, confirm it fails for the right reason (not import error, not typo).
2. **GREEN**: Write the minimal code to make the test pass.
   - If multiple tests are planned, add and pass them one at a time.
3. **REFACTOR**: Clean up while keeping tests green.
   - Run the full test file after each refactor.

### Rules
- Run tests after every change. Never assume they pass.
- If tests exist already, run them first to establish a baseline before writing new code.
- "I'll test after" is forbidden — tests written after implementation prove nothing.
- Stop if three fix attempts fail in a row; the architecture may be wrong.

---

## Step 3 — Medium/Large Task: roadmap-driven execution

### Step 3a — Pre-flight

1. Confirm working tree is clean: `git diff --stat` must be empty. If not, ask the user to commit or stash first.
2. Record base SHA: `git rev-parse HEAD`.
3. Open the roadmap file `docs/implement_roadmap/YYYY-MM-DD-{name}.md`.
4. Write the base SHA into the roadmap's Status section under `Base commit:`.
5. Update `Last updated:` to today.

### Step 3b — Execute each step

For each step in the roadmap:

1. **Read** the step's Purpose, Files, What to do, Acceptance.
2. **RED**: Write a test that encodes the Acceptance criterion (or run an existing failing test that represents the Acceptance). Confirm it fails.
3. **GREEN**: Make the minimal change described in What to do. Only touch files listed under Files.
4. **Run** the step's Acceptance command. Must pass.
5. **REFACTOR** if needed, re-run Acceptance after each refactor.
6. **Update roadmap Status**: change `- [ ] Step N: {title}` to `- [x] Step N: {title}`. Update `Last updated:`.
7. If a step fails after three attempts, stop and mark `- [!] Step N: {title} — blocked: {one-line reason}`. Surface to the user; do not skip ahead.

### Step 3c — Done Criteria

After all steps pass:

1. Run each Done Criteria check from the roadmap.
2. If all pass, flow proceeds to `code-review`.
3. If any Done Criterion fails, mark the related step `[!]`, surface to user.

---

## Output

```
[code-implement / claude] {small|roadmap} execution complete
  Tests: {N} passed, {M} failed
  Steps (if roadmap): {k}/{K} completed
  Ready for: code-review
```

**Inputs**: User request OR `docs/implement_roadmap/YYYY-MM-DD-{name}.md`
**Outputs**: Code + test files; updated roadmap Status (if applicable)
**Token**: ~3-15K (small) / ~8-30K (roadmap-driven, step-dependent)
**Composition**:
- Completes → `code-review`
- Test fails mid-way and cause unclear → `code` (debug mode)
- Small task had no roadmap → skip directly to `code-review` → `code` (commit mode)
