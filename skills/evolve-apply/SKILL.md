---
name: evolve-apply
description: Apply approved skill-spec edits from evolve-suggest — archive the current SKILL.md to skills/td-nl/history/{skill}-v{N}.md, edit the skill body, update skill-values metadata, and log the change. Triggers on "apply those improvements", "evolve the skills", or user approval of a pending proposal.
---

# evolve-apply

**Trigger**: User approves a proposal from `evolve-suggest`, or explicitly asks to improve the framework ("apply those improvements", "evolve the skills").

**Shared context**: Before running this skill, Read `skills/_shared/evolve-cycle.md` for the safety rules (one edit per session, archive before edit) and rollback mechanism.

**Process**:

## Phase 1: Read Proposals
1. Read pending proposals from `skills/td-nl/feedback-log.md § Pending Proposals`
2. If called with a specific proposal, use that; otherwise present all pending
3. For each proposal, show: skill, problem, proposed edit, evidence, risk

## Phase 2: User Approval
4. Present proposals and get explicit approval per proposal
5. User can: approve, reject, or modify each proposal

## Phase 3: Apply Edits (for each approved proposal)
6. Archive current spec: copy `skills/{skill-name}/SKILL.md` → `skills/td-nl/history/{skill-name}-v{N}.md`
7. Apply the edit to `skills/{skill-name}/SKILL.md` — for forward proposals,
   apply the prose change in the named section. For `[PROPOSE-ROLLBACK]`,
   instead overwrite `skills/{skill-name}/SKILL.md` with the contents of the
   referenced `skills/td-nl/history/{skill-name}-v{N-1}.md`.
8. Update the `skill-values/{skill-name}.md`:
   - Set `last_spec_edit` to today's date
   - Set `edit_reason` to the proposal summary
   - Set `Q_at_edit` to the current `overall` (used by the rollback gate)
9. Log to feedback-log.md (forward edit or rollback):
   ```
   - [YYYY-MM-DD] [APPLIED]   skill:{name} v{N-1}→v{N} "{edit summary}"
   - [YYYY-MM-DD] [ROLLBACK]  skill:{name} v{N}→v{N-1} reason:"{reason}"
   ```

## Phase 4: Rollback gate (defined, post-edit)
10. The rollback path is fully online: `skill-feedback`, on every subsequent
    firing of an edited skill, compares the current `Q^L` to the stamped
    `Q_at_edit`. If `Q^L` has dropped by ≥ 1.5 within 5 firings since the
    edit, `skill-feedback` writes a `[ROLLBACK-CANDIDATE]` flag. The next
    `evolve-suggest` run turns that flag into a `[PROPOSE-ROLLBACK]` proposal,
    which the user can approve back through this skill.
11. Rollbacks count against the one-edit-per-session cap (they are edits too).

## Phase 5: Evolution Report
11. Generate report:
    ```yaml
    date: "YYYY-MM-DD"
    skills_modified: ["{skill-name}"]
    proposals_approved: N
    proposals_rejected: N
    details:
      - skill: "{name}"
        change: "{description}"
        evidence_sessions: N
        pre_edit_score: X
    ```
12. Append to `config.yaml` `evolution_history`
13. Update the active root protocol if behavioral routing changed (rare)

**Outputs**: Modified skill specs + version archive + evolution log
**Token**: ~2-5K
**Composition**: Terminal for the evolution cycle
