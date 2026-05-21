---
name: writing-review
description: Simulate a conference peer review of a draft (Clarity / Novelty / Soundness / Presentation / Missing) and produce a review with Strong Accept to Reject verdict. Triggers on "review my draft", "peer review this", "simulate reviewer feedback", "thorough review".
---

# writing-review (Codex-native single-reviewer)

**Trigger**: User asks to review a draft, "what do you think of this writing?", or wants simulated peer review.

**Runtime**: Codex-native. Produce one rigorous simulated peer review directly. Do not call subagents, platform-specific slash-command executors, or cross-model reviewers.

**Process**:
1. Read the draft section/paper
2. Evaluate as a single Codex-native reviewer:
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
**Token**: ~5-15K
**Composition**: Weaknesses identified → suggest `writing-polish` for specific fixes
