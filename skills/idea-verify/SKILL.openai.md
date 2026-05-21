---
name: idea-verify
description: Check an idea's novelty by querying DBLP + arXiv + Codex analysis, then write a verdict (highly novel / somewhat novel / incremental / already exists) with closest existing work. Triggers on "is this idea novel?", "has this been done?", "check novelty", and follows idea-discover.
---

# idea-verify (Codex-native single-model)

**Trigger**: After `idea-discover`, or when user says "is this idea novel?", "has this been done?", or proposes a specific research idea.

**Runtime**: Codex-native. Verify novelty by combining hard sources and the active Codex session's analysis. Do not use platform-specific slash-command executors, cross-model MCP reviewers, or a second model reviewer.

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
   c. **Codex analysis**: In the active Codex session, compare the idea description against the collected evidence and identify:
      - The closest existing work (with paper titles and years)
      - What differentiates this idea from existing work (if anything)
      - Novelty assessment: {highly novel | somewhat novel | incremental | already exists}
      - Be specific — cite actual papers, not vague references.
3. **Synthesize verification report** for each idea:
   ```
   ### Idea: {title}
   **Novelty verdict**: {highly novel | somewhat novel | incremental | already exists}

   **Closest existing work**:
   - {paper1} ({year}) — {similarity description}
   - {paper2} ({year}) — {similarity description}

   **Differentiation**: {what makes this idea different, if anything}

   **Confidence**: {high | medium | low} — {based on search coverage}

   **Recommendation**: {pursue | refine | pivot | abandon}
   ```
4. **Update idea file**: Append verification results to `methodology/ideas/YYYY-MM-DD-discovery.md`
5. **If source evidence and Codex analysis diverge**: Flag conflicting assessments for human review

**Inputs**: Idea descriptions (from idea-discover or user-provided)
**Outputs**: Verification report appended to idea file
**Token**: ~3-6K
**Composition**:
- Novel idea confirmed → chain to `decision-analyze` (should we pursue it?)
- Idea already exists → suggest reading the existing paper via `paper-read`
- Idea needs refinement → suggest `research-explore` to find differentiation angle

## TD-NL Integration

Tracked via `skills/td-nl/skill-values/idea-verify.md`.
Key metrics for TD assessment: were novelty assessments accurate? did search find relevant prior work? did source evidence support the final verdict?
