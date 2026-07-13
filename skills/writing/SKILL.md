---
name: writing
description: Paper prose production in one mode-based skill — OUTLINE (section structure, page budget, figure plan, and a Claims-Evidence Matrix mapping every claim to its evidence), DRAFT (write a section in venue-appropriate LaTeX with citation auto-verification via citation_fetch.py), POLISH (tighten specific text with before/after). Absorbs the former writing-outline / writing-draft / writing-polish skills — those names now refer to modes here. Peer review stays a separate skill (`writing-review`, codex-track variants). Triggers on "outline the paper", "draft the introduction", "write the method section", "polish this paragraph", "make this clearer".
---

# writing

Review of drafted text is the separate `writing-review` skill (it ships
codex-track variants). Chain: OUTLINE → DRAFT → `writing-review` → POLISH.

## Mode: OUTLINE — "how should I organize the paper?", new paper

1. Read existing outputs: `paper/`, `methodology/approach.md`,
   `RESEARCH_STATE.md § Established evidence` (what claims are actually
   supported).
2. Propose: section structure with page estimates, 2-3 content bullets per
   section, figure/table plan, mapping of existing artifacts → sections.
3. Emit the **Claims-Evidence Matrix** — every intended claim gets a row:
   `| # | Claim | Evidence type | Source | Status (have/need) |`
   A claim's `Source` should point at real evidence (run id, proof file,
   analysis) — `RESEARCH_STATE.md` is the ledger of what is `have`.
4. Identify gaps: research needed before each section is writable.
5. Save to `paper/papers/outline.md` on confirmation.

## Mode: DRAFT — "draft the introduction / method / results"

1. Read the outline + sources: `paper/proofs/`, `paper/theory/`,
   `resources/papers/*.md`, relevant run summaries.
2. **Only write claims whose matrix status is `have`** — flag `need` claims
   to the user instead of papering over them; never upgrade evidence
   strength in prose ("suggests" stays "suggests" for weak-stamped runs).
3. Draft in venue-appropriate LaTeX with `\cite{author_year}` placeholders;
   integrate figures/tables where the plan says.
4. Save to `paper/papers/{section}.tex`, then **verify citations**: for each
   placeholder run `scripts/citation_fetch.py "{title}" --authors "{author}"`;
   replace with the verified BibTeX key or mark `% [VERIFY]`; append entries
   to `paper/papers/references.bib`. Report
   `Citations: {N} verified, {M} need manual verification`.
→ suggest `writing-review`.

## Mode: POLISH — "make this clearer", "tighten this paragraph"

Improve sentence structure, flow, technical precision, conciseness,
transitions. Present original vs polished side-by-side with the key changes
explained. Standalone — typically doesn't chain.

**Inputs**: outline/section name/text + sources + target venue
**Outputs**: `paper/papers/outline.md`, `paper/papers/{section}.tex` +
`references.bib`; polish inline
**Token**: OUTLINE 2-5K · DRAFT 5-15K · POLISH 2-5K
**Composition**: matrix `need` rows → `experiment-plan` or `proof`;
completed sections → `paper-compile`; drafted claims tracked as deliverables
→ `checklist` (update mode).
