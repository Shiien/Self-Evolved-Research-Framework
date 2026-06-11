---
name: idea-verify
description: Check an idea's novelty by querying DBLP + arXiv + a Claude subagent + a Codex reviewer (GPT-5.5 via `mcp__codex__codex`), then write a verdict (highly novel / somewhat novel / incremental / already exists) with closest existing work. The Codex source catches prior work published after Claude's training cutoff. Triggers on "is this idea novel?", "has this been done?", "check novelty", and follows idea-discover.
---

# idea-verify (codex track)

**Trigger**: After `idea-discover`, or when user says "is this idea novel?", "has this been done?", or proposes a specific research idea.

**Shared context**: Before acting, Read `skills/_shared/cross-model-review.md` for the MCP invocation contract (§1), 4-source synthesize decision procedure (§2.2), and fallback when Codex is unavailable (§3).

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
   c. **Claude subagent verification** (upstream path, retained):
      - Launch `Agent(subagent_type="general-purpose")` with:
        - The idea description to verify
        - Instructions:
          ```
          You are a research novelty checker. Given an idea description, identify:
          1. The closest existing work (with paper titles and years)
          2. What differentiates this idea from existing work (if anything)
          3. Novelty assessment: {highly novel | somewhat novel | incremental | already exists}
          Be specific — cite actual papers, not vague references.
          ```
   d. **Codex cross-family verification** (new on codex track) — in parallel with step 2c:
      - Invoke `mcp__codex__codex` per `_shared/cross-model-review.md § 1`. Call body:
        - **Role**: "You are a research novelty checker with knowledge of recent ML/systems literature."
        - **Artifact**: full idea description, key claims, technical approach keywords (same as step 2c input)
        - **Output schema** (must match step 2c's 3-item format so synthesize is symmetric):
          ```
          1. The closest existing work (with paper titles and years)
          2. What differentiates this idea from existing work (if anything)
          3. Novelty assessment: {highly novel | somewhat novel | incremental | already exists}
          ```
        - **Directive tail**: "Be specific — cite actual papers, not vague references. Focus on work published in the last 2 years, where your training data is stronger than Claude's. Do not reference any prior opinion — form your own judgment."
      - If the call fails or times out, follow `_shared/cross-model-review.md § 3` (fallback): skip step 2d, proceed with 3-source synthesize (DBLP + arXiv + Claude subagent), and annotate the final report.

3. **4-source synthesize** per `_shared/cross-model-review.md § 2.2`:
   - Apply the decision procedure:
     1. Hard sources (DBLP/arXiv) find direct match → verdict `already exists` or `incremental`; soft sources (c/d) only refine the citation list
     2. Hard sources empty but c AND d both say "already exists / incremental" → `incremental` with Medium confidence; surface both soft-source citations
     3. Hard sources empty, c and d disagree → `somewhat novel` with Low confidence; flag for human with both opinions
     4. All four empty → `highly novel` with High confidence (Codex/GPT-5.5 later training cutoff strengthens this)
   - Merge "closest existing work" list by deduplication on (title, year); tag each paper with its source(s)

   Report format:
   ```
   ---
   cross_model: true
   claude_subagent: ok
   codex: ok
   synthesize_mode: 4-source
   ---
   ### Idea: {title}
   **Novelty verdict**: {highly novel | somewhat novel | incremental | already exists}

   **Closest existing work** (dedup + source-tagged):
   - {paper1} ({year}) — {similarity description}  — [DBLP, Codex]
   - {paper2} ({year}) — {similarity description}  — [arXiv]
   - {paper3} ({year}) — {similarity description}  — [Claude subagent]
   - {paper4} ({year}) — {similarity description}  — [Codex only — likely post-Claude cutoff]

   **Differentiation**: {what makes this idea different, if anything}

   **Confidence**: {high | medium | low} — {based on search coverage + cross-source agreement}

   **Source-level agreement**:
   - DBLP hit count: {N}
   - arXiv hit count: {N}
   - Claude subagent verdict: {verdict}
   - Codex verdict: {verdict}
   - Agreement: {all-agree | hard-vs-soft split | soft-only disagreement}

   **Recommendation**: {pursue | refine | pivot | abandon}
   ```

4. **Update idea file**: Append verification results to `methodology/ideas/YYYY-MM-DD-discovery.md` (same location as upstream — see `_shared/cross-model-review.md § 4`).

5. **If any pair of sources disagrees**: flag conflicting assessments for human review — specifically highlight "Codex-only" findings (papers only Codex knows) as these are most likely to be **post-Claude-cutoff prior work** that refutes novelty.

**Inputs**: Idea descriptions (from idea-discover or user-provided)
**Outputs**: Verification report appended to idea file
**Token**: ~3-6K (upstream) / ~5-9K (codex track — one extra MCP call per idea, no loop)
**Composition**:
- Novel idea confirmed → chain to `decision-analyze` (should we pursue it?)
- Idea already exists → suggest reading the existing paper via `paper-read`
- Idea needs refinement → suggest `research-explore` to find differentiation angle

## TD-NL Integration

Tracked via `skills/td-nl/skill-values/idea-verify.md`.
Upstream key metrics: were novelty assessments accurate? did search find relevant prior work? cross-model agreement level?
Codex track adds: `codex_agreement_rate_with_hard_sources` (how often Codex's verdict aligns with DBLP/arXiv evidence — calibration check) and `codex_unique_hits` (papers only Codex cited that turned out to be real prior work — the direct value signal).
