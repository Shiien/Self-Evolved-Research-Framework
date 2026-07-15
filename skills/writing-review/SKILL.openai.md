---
name: writing-review
description: Use when a draft, paper section, or full manuscript needs peer-review feedback, venue-readiness assessment, or a challenge to its claims and evidence.
---

# writing-review

**Trigger**: The user asks for a draft review, simulated peer review, or venue-readiness assessment.

**Runtime**: The active Codex session performs one rigorous review directly.

## Process

1. Read the draft and identify its stated contributions, evidence, assumptions, and target venue.
2. Evaluate:
   - **Clarity**: Are the problem, method, and claims understandable?
   - **Novelty**: Is the contribution differentiated and accurately scoped?
   - **Soundness**: Do the method and evidence support the conclusions?
   - **Presentation**: Are organization, figures, tables, and terminology effective?
   - **Missing**: What evidence, baselines, limitations, or explanations would reviewers expect?
3. Produce a conference-style review:
   - Summary in two or three sentences
   - Specific strengths
   - Prioritized weaknesses with actionable suggestions
   - Questions for the authors
   - Overall verdict: Strong Accept / Accept / Borderline / Reject
   - Confidence: High / Medium / Low
4. Cite exact sections or passages for every material criticism.
5. Output inline, or save to `paper/reviews/` for a full-paper review when a durable artifact is appropriate.

Do not silently edit the draft during review. If changes are requested after the verdict, continue with `writing` (POLISH mode).

**Inputs**: Draft text and target venue

**Outputs**: Structured review inline or in `paper/reviews/`

**Composition**: Weaknesses identified → `writing` (POLISH mode)
