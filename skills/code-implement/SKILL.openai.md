---
name: code-implement
description: Use when the user asks to implement a feature, fix a bug, modify code behavior, or execute an approved implementation roadmap.
---

# code-implement

**Trigger**: The user wants to write new code or modify existing code.

**Shared context**: None at this stage; if a roadmap is used, that file carries the specification.

**Runtime**: The active Codex session implements directly with strict TDD.

---

## Step 0 — Red Flags

Stop and reconsider if any of these thoughts appear:

| Thought | Reality |
|---------|---------|
| "This is just simple code" | Simple things become complex. Use TDD. |
| "I'll test after" | Tests written after implementation pass immediately and prove nothing. |
| "Should work now" | Not verification. Run the command and read the output. |
| "Too simple for review" | All code gets reviewed. No exceptions. |
| "Let me explore first" | TDD is the exploration. Write a failing test. |
| "Three fixes failed; let me try once more" | The architecture may be wrong. Stop and discuss. |

---

## Step 1 — Size Assessment

Estimate the scope:

| Signal | Path |
|--------|------|
| Localized change, single file, less than about 30 lines of new logic | **Small** → Step 2 |
| New module, multiple files, or significant new logic | **Medium/Large** → Step 3 |
| User explicitly requests a plan or design review | **Medium/Large** → Step 3 |
| Change touches SER framework files such as `.agents/`, `skills/`, `config.yaml`, or `AGENTS.md` | **Small + direct handling** → Step 2 |

Default to **Small**. When uncertainty would materially change the work, ask whether to implement directly or write a roadmap first.

If the task is Medium/Large and no roadmap exists, use `code` in ROADMAP mode first, then return here.

---

## Step 2 — Small Task: Single TDD Cycle

Follow this sequence without exception:

1. **RED**: Write a failing test that defines the expected behavior.
   - Put the test next to the source or in the repository's test mirror.
   - Run it and confirm it fails for the intended reason, not an import error or typo.
2. **GREEN**: Write the minimum code needed to make the test pass.
   - If multiple tests are needed, add and pass them one at a time.
3. **REFACTOR**: Clean up while keeping tests green.
   - Run the full relevant test file after each refactor.

### Rules

- Run existing relevant tests first to establish a baseline.
- Run tests after every behavior change; never assume they pass.
- Tests written only after implementation are forbidden.
- Stop after three failed fix attempts and discuss the architectural issue.

---

## Step 3 — Medium/Large Task: Roadmap-Driven Execution

### Step 3a — Pre-flight

1. Inspect the working tree and preserve unrelated user changes.
2. Record the base SHA with `git rev-parse HEAD`.
3. Open `docs/implement_roadmap/YYYY-MM-DD-{name}.md`.
4. Record the base SHA and update date in the roadmap's Status section.

### Step 3b — Execute Each Step

For every roadmap step:

1. Read its Purpose, Files, What to do, and Acceptance sections.
2. **RED**: Add or run a test that represents Acceptance and confirm the expected failure.
3. **GREEN**: Make the minimum specified change, touching only authorized files.
4. Run the Acceptance command and require a pass.
5. Refactor if needed, rerunning Acceptance after every refactor.
6. Mark the step complete in roadmap Status and update the date.
7. After three failed attempts, mark the step blocked, report the reason, and stop.

### Step 3c — Done Criteria

After all steps pass:

1. Run every Done Criteria check in the roadmap.
2. If all checks pass, continue to `code-review`.
3. If a check fails, mark the related step blocked and report it.

---

## Output

```text
[code-implement / codex] {small|roadmap} execution complete
  Tests: {N} passed, {M} failed
  Steps (if roadmap): {k}/{K} completed
  Ready for: code-review
```

**Inputs**: User request or `docs/implement_roadmap/YYYY-MM-DD-{name}.md`

**Outputs**: Code and test changes; updated roadmap status when applicable

**Composition**:

- Completes → `code-review`
- Failure cause is unclear → `code` (DEBUG mode)
- Review passes → `code` (COMMIT mode)
