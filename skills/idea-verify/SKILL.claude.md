---
name: idea-verify
description: Use when a research idea needs a novelty check, a defensible comparison with prior work, or verification after `idea` (DISCOVER mode).
---

# idea-verify

**Trigger**: After `idea` (DISCOVER mode), or when user says "is this idea novel?", "has this been done?", or proposes a specific research idea.

**Runtime**: The active Claude session performs source retrieval, comparison, and judgment directly.

**Process**:
1. **Extract verification targets**: For each idea to verify, extract:
   - Key claims / core contribution
   - Technical approach keywords
   - Expected related work search terms
2. **Automated search** (multi-source):
   a. **DBLP search**: Query `https://dblp.org/search/publ/api?q={keywords}&format=json`
      - Look for papers with similar titles or approaches
   b. **arXiv search** (via export API): Query `http://export.arxiv.org/api/query?search_query={keywords}&max_results=10`
      - Check recent papers (last 2 years) in relevant categories
   c. **Source-grounded analysis** in the active session:
      - Identify the closest existing work with paper titles and years
      - Separate goal overlap from mechanism overlap
      - State what differentiates the proposed idea, if anything
      - Assign a novelty assessment only after checking the primary sources
3. **Synthesize verification report** for each idea:
   ```
   ### Idea: {title}
   **Novelty verdict**: {highly-novel | somewhat-novel | incremental | low | already-exists}

   **Closest existing work**:
   - {paper1} ({year}) — {similarity description}
   - {paper2} ({year}) — {similarity description}

   **Differentiation**: {what makes this idea different, if anything}

   **Confidence**: {high | medium | low} — {based on search coverage}

   **Recommendation**: {pursue | refine | pivot | abandon}
   ```
4. **Persist one machine-readable result per idea** under that idea's `Verification Results` entry in `methodology/ideas/YYYY-MM-DD-discovery.md` (or the discovery file that owns it).

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
5. **If source evidence conflicts or coverage is incomplete**: Mark the result incomplete, lower confidence, and flag the unresolved question for human review.

**Inputs**: Idea descriptions (from `idea` DISCOVER mode or user-provided)
**Outputs**: Verification report persisted per idea for `idea` (REFINE mode)
**Token**: ~3-6K
**Composition**:
- Novel idea confirmed → chain to `decision-analyze` (should we pursue it?)
- Idea already exists → suggest reading the existing paper via `paper-read`
- Idea needs refinement → suggest `idea` (EXPLORE mode) to find a differentiation angle

## TD-NL Integration

Tracked via `skills/td-nl/skill-values/idea-verify.md`.
Key metrics for TD assessment: were novelty assessments accurate? did search find relevant prior work? did source evidence support the final verdict?
