---
name: idea-verify
description: Use when a research idea needs a novelty check, a defensible comparison with prior work, or verification after `idea` (DISCOVER mode).
---

# idea-verify

**Trigger**: The user asks whether a research idea is novel, whether it has been done, or requests verification after `idea` (DISCOVER mode).

**Runtime**: The active Codex session performs source retrieval, comparison, and judgment directly.

## Process

1. **Extract verification targets** for each idea:
   - Core contribution and falsifiable novelty claims
   - Technical approach and assumed differentiators
   - Related-work keywords, synonyms, and likely predecessor methods
2. **Search current primary sources**:
   - Query DBLP for bibliographic coverage.
   - Query arXiv and relevant publisher or conference indexes for recent work.
   - Prefer original papers and official proceedings over summaries.
3. **Verify candidates**:
   - Read enough of each candidate to confirm the method, not just title similarity.
   - Separate identical goals from identical mechanisms.
   - Record publication year, stable link, overlap, and material differences.
4. **Synthesize a verdict for each idea**:

   ```markdown
   ### Idea: {title}
   **Novelty verdict**: {highly-novel | somewhat-novel | incremental | low | already-exists}

   **Closest existing work**:
   - {paper} ({year}) — {verified overlap}

   **Differentiation**: {what remains distinct, if anything}
   **Confidence**: {high | medium | low} — {coverage and limitations}
   **Recommendation**: {pursue | refine | pivot | abandon}
   ```

5. **Persist one machine-readable result per idea** under that idea's `Verification Results` entry in `methodology/ideas/YYYY-MM-DD-discovery.md` (or the discovery file that owns it).

   After primary-source verification is complete, write:

   ```yaml
   verification_status: complete
   verified_by: idea-verify
   verification_date: YYYY-MM-DD
   novelty_verdict: "<highly-novel|somewhat-novel|incremental|low|already-exists>"
   verification_sources:
     - id: "<DOI, arXiv ID, or official proceedings ID>"
       url: "<primary-source URL>"
   ```

   `verification_sources` must contain at least one primary-source identifier or URL actually used to determine the verdict. A `low` or `already-exists` verdict is still a completed verification and therefore includes `verified_by: idea-verify`; `idea` (REFINE mode) will block refinement based on the verdict.

   If retrieval fails, coverage is inadequate, or the evidence cannot support a verdict, write an incomplete block and omit `verified_by` entirely rather than setting it to an empty or null value:

   ```yaml
   verification_status: incomplete
   verification_date: YYYY-MM-DD
   novelty_verdict: inconclusive
   verification_sources: []
   incomplete_reason: "<missing source or unresolved evidence>"
   ```

   For multiple ideas, append a separate result block inside each idea's own `Verification Results` entry. Never write one top-level `verified_by` marker for a batch with different verdicts.
6. **Expose uncertainty**: State what must be checked next for every incomplete result.

Never infer novelty from absence in one search query. Never cite a paper that was not verified from a primary source.

**Inputs**: Idea from the user or `idea` (DISCOVER mode)

**Outputs**: Source-backed novelty report persisted per idea for `idea` (REFINE mode)

**Composition**:

- Novel idea confirmed → `decision-analyze`
- Existing method found → `paper-read`
- Differentiation is weak → `idea` (EXPLORE mode)

## TD-NL Integration

Track whether the search found the relevant prior work, whether cited evidence supports the verdict, and whether later feedback confirms the assessment in `skills/td-nl/skill-values/idea-verify.md`.
