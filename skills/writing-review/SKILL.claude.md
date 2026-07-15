---
name: writing-review
description: Use when a draft, paper section, or full manuscript needs peer-review feedback, venue-readiness assessment, or a challenge to its claims and evidence.
---

# writing-review

**Trigger**: User asks to review a draft, "what do you think of this writing?", or wants simulated peer review.

**Runtime**: The active Claude session performs one rigorous review directly.

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
**Token**: ~5-15K
**Composition**: Weaknesses identified → suggest `writing` (POLISH mode) for specific fixes

## TD-NL Integration

Track review usefulness, correctness of identified weaknesses, and downstream acceptance of the recommendations in `skills/td-nl/skill-values/writing-review.md`.
