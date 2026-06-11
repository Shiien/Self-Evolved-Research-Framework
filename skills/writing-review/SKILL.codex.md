---
name: writing-review
description: Simulate a conference peer review of a draft (Clarity / Novelty / Soundness / Presentation / Missing) and produce a review with Strong Accept to Reject verdict. Runs in cross-model adversarial mode with TWO external reviewers — a Claude subagent (upstream) and a Codex reviewer (GPT-5.5 via `mcp__codex__codex`) — for true cross-family independence, plus an auto-fix loop (max 3 rounds on codex track). Triggers on "review my draft", "peer review this", "simulate reviewer feedback", "thorough review".
---

# writing-review (codex track)

**Trigger**: User asks to review a draft, "what do you think of this writing?", or wants simulated peer review.

**Process**:
1. Read the draft section/paper
2. Evaluate from multiple reviewer perspectives:
   - **Clarity**: Is the writing clear? Are claims well-supported?
   - **Novelty**: Is the contribution clearly articulated?
   - **Soundness**: Are the technical claims correct?
   - **Presentation**: Figures, organization, flow
   - **Missing**: What's absent that reviewers would expect?
3. Generate review in conference format:
   - Summary (2-3 sentences)
   - Strengths (bulleted)
   - Weaknesses (bulleted, with specific suggestions)
   - Questions for authors
   - Overall: Strong Accept / Accept / Borderline / Reject
4. Output inline (save to `paper/reviews/` if full paper review)

**Inputs**: Draft text + target venue
**Outputs**: Structured review (inline or saved)
**Token**: ~5-15K (single-model) / ~15-35K (3-way cross-model loop with auto-fix)
**Composition**: Weaknesses identified → suggest `writing-polish` for specific fixes

## Cross-Model Review Mode (codex track)

When cross-model feedback is desired, `writing-review` operates in **3-way cross-model adversarial mode**: Claude主 evaluates internally, a Claude subagent reviews independently, and a Codex/GPT-5.5 reviewer adds a true out-of-family perspective. Suggested for full paper reviews or critical sections (introduction, methodology).

**Shared context**: Before acting, Read `skills/_shared/cross-model-review.md` for the MCP invocation contract (§1), 3-way synthesize rules (§2.1), fallback when Codex is unavailable (§3), output conventions (§4), and loop-round budget (§5).

**Activation**: Auto-activated when reviewing full papers or when user requests "thorough review" / "adversarial review". Can be explicitly requested or skipped.

**Process**:

1. **Send draft to Claude subagent reviewer** (same as upstream):
   - Launch `Agent(subagent_type="general-purpose")` with:
     - The draft text
     - System instructions:
       ```
       You are a rigorous peer reviewer for {venue}. Review this paper section with the standards of a top-tier venue. Provide:
       1. Summary (2-3 sentences)
       2. Strengths (bulleted, specific)
       3. Weaknesses (bulleted, with concrete fix suggestions)
       4. Questions for authors
       5. Score: {Strong Accept / Accept / Borderline / Reject}
       6. Confidence: {High / Medium / Low}
       Be critical but constructive. Cite specific passages.
       ```

2. **Send draft to Codex reviewer** (new on codex track) — in parallel with step 1:
   - Invoke `mcp__codex__codex` per `_shared/cross-model-review.md § 1`. Call body:
     - **Role**: "You are a rigorous peer reviewer for {venue} at a top-tier venue."
     - **Artifact**: full draft text
     - **Project context**: 1–2 sentences on methodology/goals from `config.yaml` or user context
     - **Output schema** (must match upstream subagent's 6-item format so synthesize is symmetric):
       ```
       1. Summary (2-3 sentences)
       2. Strengths (bulleted, specific)
       3. Weaknesses (bulleted, with concrete fix suggestions)
       4. Questions for authors
       5. Score: {Strong Accept / Accept / Borderline / Reject}
       6. Confidence: {High / Medium / Low}
       ```
     - **Directive tail**: "Be critical but constructive. Cite specific passages. Do not reference any prior review — form your own judgment."
   - If the call fails or times out, follow `_shared/cross-model-review.md § 3` (fallback): skip the Codex reviewer for this run, continue with Claude subagent only, and annotate the final report.

3. **Internal review**: Simultaneously generate own review (standard writing-review process). Do not read the subagent's or Codex's output while forming this review.

4. **3-way Synthesize** per `_shared/cross-model-review.md § 2.1`:
   - Classify each finding by agreement pattern (All 3 / 2-vs-1 variants / All disagree)
   - Pay special attention to "2-vs-1 with Claude主+subagent majority, Codex dissent" — this is often a Claude-family blind spot and should be included in the fix list with a "Codex-only concern" tag
   - External score for stopping = `min(claude_subagent_score, codex_score)`

5. **Auto-fix loop** (max **3 rounds** on codex track — reduced from upstream 4 due to double external-reviewer cost per round, per `_shared/cross-model-review.md § 5`):
   - Round N: Apply fixes for ALL-3-agree and 2-external-agree findings (skip Claude主-only findings that both externals reject)
   - Re-submit revised draft to BOTH Claude subagent AND Codex reviewer with: "I've addressed your feedback. Here's the revised version: {diff summary}. Please re-review."
   - Track 3 score trajectories — subagent and codex each have their own curve
   - **Stopping criteria** (tightened for 3-way):
     - BOTH external scores (subagent AND codex) reach "Accept" or better → stop
     - BOTH external scores unchanged for 2 consecutive rounds → stop (diminishing returns)
     - 3 rounds reached → stop (hard cap)
     - Codex unavailable for this round AND subagent score already unchanged 2 rounds → stop
     - User interrupts → stop

6. **Output**: Final synthesized review + revision history, following `_shared/cross-model-review.md § 4` output conventions (YAML header with `cross_model: true`, per-finding source attribution):
   ```
   ---
   cross_model: true
   claude_subagent: ok
   codex: ok
   synthesize_mode: 3-way
   ---
   ## Cross-Model Review Summary
   Rounds: {N}
   Score trajectory (Claude subagent): {R1: Reject → R2: Borderline → R3: Accept}
   Score trajectory (Codex):           {R1: Borderline → R2: Accept → R3: Accept}
   Key improvements made: {bulleted list, each tagged with source e.g. "(All 3)", "(Codex only)", "(Claude subagent + Codex)"}
   Remaining issues: {what couldn't be auto-fixed, attributed}
   Agreement profile: all-3={X}%, 2-vs-1={Y}%, all-disagree={Z}%
   ---
   ```

7. Save review to `paper/reviews/{section_name}-cross-review.md` (same path as upstream — see `_shared/cross-model-review.md § 4`).

**TD-NL tracking**: Performance tracked via `skills/td-nl/skill-values/writing-review.md`.
Codex track adds two metrics: `codex_agreement_rate` (how often Codex agrees with Claude subagent) and `codex_availability` (fraction of rounds where Codex was reachable). If Codex agreement is consistently high (>90%) across sessions, future optimization may swap Codex in/out based on cost; if consistently low, the Codex signal is genuinely additive and should be kept.
Upstream metrics continue: rounds-to-accept, score improvement per round, agreement rate with internal review.
